import asyncio
import json
from fastapi import HTTPException
from typing import Optional, AsyncGenerator, Dict, Any
from openai import AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai._exceptions import APIError, RateLimitError, AuthenticationError, BadRequestError

class OpenAIClient:
    """Async OpenAI client with cancellation support and multi-endpoint routing."""

    def __init__(self, api_key: str, base_url: str, timeout: int = 90, api_version: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None):
        # Basic validation for custom headers
        if custom_headers is not None:
            if not isinstance(custom_headers, dict):
                raise ValueError("custom_headers must be a dictionary")
            if not all(isinstance(k, str) and isinstance(v, str) for k, v in custom_headers.items()):
                raise ValueError("custom_headers must contain only string keys and values")

        self.default_api_key = api_key
        self.default_base_url = base_url
        self.default_api_version = api_version
        self.timeout = timeout
        self.custom_headers = custom_headers

        # Single default client for backward compatibility
        self.client = self._create_client(api_key, base_url, api_version, custom_headers)

        # Per-model clients for hybrid deployments
        self.big_client = None
        self.middle_client = None
        self.small_client = None

        self.active_requests: Dict[str, asyncio.Event] = {}

    def _create_client(self, api_key: str, base_url: str, api_version: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None):
        """Create an OpenAI or Azure client."""
        if api_version:
            return AsyncAzureOpenAI(
                api_key=api_key,
                azure_endpoint=base_url,
                api_version=api_version,
                timeout=self.timeout,
                default_headers=custom_headers
            )
        else:
            return AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self.timeout,
                default_headers=custom_headers
            )

    def configure_per_model_clients(self, config):
        """Configure per-model clients for hybrid deployments."""
        # Big model client
        if config.enable_big_endpoint:
            self.big_client = self._create_client(
                config.big_api_key,
                config.big_endpoint,
                config.azure_api_version if config.big_endpoint == config.openai_base_url else None,
                self.custom_headers
            )

        # Middle model client
        if config.enable_middle_endpoint:
            self.middle_client = self._create_client(
                config.middle_api_key,
                config.middle_endpoint,
                config.azure_api_version if config.middle_endpoint == config.openai_base_url else None,
                self.custom_headers
            )

        # Small model client
        if config.enable_small_endpoint:
            self.small_client = self._create_client(
                config.small_api_key,
                config.small_endpoint,
                config.azure_api_version if config.small_endpoint == config.openai_base_url else None,
                self.custom_headers
            )

    def get_client_for_model(self, model: str, config=None) -> Any:
        """Get the appropriate client for a model (BIG, MIDDLE, or SMALL)."""
        # Check for exact model matches first
        if self.big_client and config and model == config.big_model:
            return self.big_client
        if self.middle_client and config and model == config.middle_model:
            return self.middle_client
        if self.small_client and config and model == config.small_model:
            return self.small_client

        # Fallback to default client
        return self.client
    
    async def create_chat_completion(self, request: Dict[str, Any], request_id: Optional[str] = None, config=None, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Send chat completion to OpenAI API with cancellation support.

        Args:
            request: OpenAI request dictionary
            request_id: Optional request ID for cancellation tracking
            config: Optional config object
            api_key: Optional per-request API key (for passthrough mode)
        """
        
        # Check for Antigravity models - route to Antigravity client
        model = request.get('model', '')
        if model.lower().startswith('antigravity/') or 'antigravity' in model.lower():
            from src.services.antigravity_client import get_antigravity_client
            from src.services.models.provider_detector import ProviderDetector
            
            # Normalize model name for Antigravity
            detector = ProviderDetector("https://daily-cloudcode-pa.sandbox.googleapis.com")
            antigravity_model = detector.normalize_model_name(model)
            
            client = get_antigravity_client()
            return await client.create_chat_completion(
                messages=request.get('messages', []),
                model=antigravity_model,
                max_tokens=request.get('max_tokens', request.get('max_completion_tokens', 8192)),
                temperature=request.get('temperature', 1.0),
                stream=False
            )

        # Get the appropriate client based on the model
        # If api_key is provided (passthrough mode), create a temporary client
        if api_key:
            client = self._create_client(
                api_key,
                config.openai_base_url if config else self.default_base_url,
                config.azure_api_version if config else self.default_api_version,
                self.custom_headers
            )
        else:
            client = self.get_client_for_model(request.get('model', ''), config)

        # Create cancellation token if request_id provided
        if request_id:
            cancel_event = asyncio.Event()
            self.active_requests[request_id] = cancel_event

        try:
            # Create task that can be cancelled
            completion_task = asyncio.create_task(
                client.chat.completions.create(**request)
            )

            if request_id:
                # Wait for either completion or cancellation
                cancel_task = asyncio.create_task(cancel_event.wait())
                done, pending = await asyncio.wait(
                    [completion_task, cancel_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                # Check if request was cancelled
                if cancel_task in done:
                    completion_task.cancel()
                    raise HTTPException(status_code=499, detail="Request cancelled by client")

                completion = await completion_task
            else:
                completion = await completion_task

            # Convert to dict format that matches the original interface
            return completion.model_dump()

        except AuthenticationError as e:
            raise HTTPException(status_code=401, detail=self.classify_openai_error(str(e)))
        except RateLimitError as e:
            raise HTTPException(status_code=429, detail=self.classify_openai_error(str(e)))
        except BadRequestError as e:
            raise HTTPException(status_code=400, detail=self.classify_openai_error(str(e)))
        except APIError as e:
            status_code = getattr(e, 'status_code', 500)
            raise HTTPException(status_code=status_code, detail=self.classify_openai_error(str(e)))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        finally:
            # Clean up active request tracking
            if request_id and request_id in self.active_requests:
                del self.active_requests[request_id]
    
    async def create_chat_completion_stream(self, request: Dict[str, Any], request_id: Optional[str] = None, config=None, api_key: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Send streaming chat completion to OpenAI API with cancellation support.

        Args:
            request: OpenAI request dictionary
            request_id: Optional request ID for cancellation tracking
            config: Optional config object
            api_key: Optional per-request API key (for passthrough mode)
        """
        
        # Check for Antigravity models - route to Antigravity client
        model = request.get('model', '')
        if model.lower().startswith('antigravity/') or 'antigravity' in model.lower():
            from src.services.antigravity_client import get_antigravity_client
            from src.services.models.provider_detector import ProviderDetector
            
            # Normalize model name for Antigravity
            detector = ProviderDetector("https://daily-cloudcode-pa.sandbox.googleapis.com")
            antigravity_model = detector.normalize_model_name(model)
            
            client = get_antigravity_client()
            async for chunk in client.create_chat_completion_stream(
                messages=request.get('messages', []),
                model=antigravity_model,
                max_tokens=request.get('max_tokens', request.get('max_completion_tokens', 8192)),
                temperature=request.get('temperature', 1.0)
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}"
            yield "data: [DONE]"
            return

        # Get the appropriate client based on the model
        # If api_key is provided (passthrough mode), create a temporary client
        if api_key:
            client = self._create_client(
                api_key,
                config.openai_base_url if config else self.default_base_url,
                config.azure_api_version if config else self.default_api_version,
                self.custom_headers
            )
        else:
            client = self.get_client_for_model(request.get('model', ''), config)

        # Create cancellation token if request_id provided
        if request_id:
            cancel_event = asyncio.Event()
            self.active_requests[request_id] = cancel_event

        try:
            # Ensure stream is enabled
            request["stream"] = True
            if "stream_options" not in request:
                request["stream_options"] = {}
            request["stream_options"]["include_usage"] = True

            # Create the streaming completion
            streaming_completion = await client.chat.completions.create(**request)

            async for chunk in streaming_completion:
                # Check for cancellation before yielding each chunk
                if request_id and request_id in self.active_requests:
                    if self.active_requests[request_id].is_set():
                        raise HTTPException(status_code=499, detail="Request cancelled by client")

                # Convert chunk to SSE format matching original HTTP client format
                chunk_dict = chunk.model_dump()
                chunk_json = json.dumps(chunk_dict, ensure_ascii=False)
                yield f"data: {chunk_json}"

            # Signal end of stream
            yield "data: [DONE]"

        except AuthenticationError as e:
            raise HTTPException(status_code=401, detail=self.classify_openai_error(str(e)))
        except RateLimitError as e:
            raise HTTPException(status_code=429, detail=self.classify_openai_error(str(e)))
        except BadRequestError as e:
            raise HTTPException(status_code=400, detail=self.classify_openai_error(str(e)))
        except APIError as e:
            status_code = getattr(e, 'status_code', 500)
            raise HTTPException(status_code=status_code, detail=self.classify_openai_error(str(e)))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

        finally:
            # Clean up active request tracking
            if request_id and request_id in self.active_requests:
                del self.active_requests[request_id]

    def classify_openai_error(self, error_detail: Any) -> str:
        """Provide specific error guidance for common API issues."""
        error_str = str(error_detail).lower()

        # Debug logging for error classification
        print(f"DEBUG: Classifying error: {error_str}")

        # Region/country restrictions
        if "unsupported_country_region_territory" in error_str or "country, region, or territory not supported" in error_str:
            return "API is not available in your region. Consider using a VPN or different provider."

        # API key issues
        if "invalid_api_key" in error_str or "unauthorized" in error_str or "user not found" in error_str:
            return "Invalid API key or user not found. Please check your OPENAI_API_KEY configuration and ensure your provider account is active. Note: OPENAI_API_KEY is used for any provider (OpenRouter, OpenAI, Azure, etc.)"

        # Rate limiting
        if "rate_limit" in error_str or "quota" in error_str:
            return "Rate limit exceeded. Please wait and try again, or upgrade your API plan with your provider."

        # Model not found
        if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
            return "Model not found. Please check your BIG_MODEL and SMALL_MODEL configuration."

        # Billing issues
        if "billing" in error_str or "payment" in error_str:
            return "Billing issue. Please check your provider account billing status."

        # Default: return original message
        return str(error_detail)
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request by request_id."""
        if request_id in self.active_requests:
            self.active_requests[request_id].set()
            return True
        return False