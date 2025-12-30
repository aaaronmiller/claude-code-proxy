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
        import time
        timestamp = time.strftime("%H:%M:%S")
        
        # Special handling for VibeProxy (Antigravity's local proxy on port 8317)
        is_vibeproxy = "127.0.0.1:8317" in base_url or "localhost:8317" in base_url
        
        if is_vibeproxy:
            # VibeProxy requires Antigravity's OAuth token, not OpenRouter/OpenAI keys
            from src.services.antigravity import get_antigravity_token
            
            print(f"DEBUG [VibeProxy {timestamp}]: CLIENT CREATION for VibeProxy - Fetching Antigravity token...")
            antigravity_token = get_antigravity_token()
            if antigravity_token:
                print(f"DEBUG [VibeProxy {timestamp}]: Token retrieved successfully (first 20 chars): {antigravity_token[:20]}...")
                api_key = antigravity_token
            else:
                print(f"ERROR [VibeProxy {timestamp}]: No Antigravity token found! Authentication will FAIL.")
                print(f"ERROR [VibeProxy {timestamp}]: Please ensure you're logged into Antigravity IDE.")
            
        # Diagnostic logging for VibeProxy authentication
        if is_vibeproxy:
            print(f"DEBUG [VibeProxy {timestamp}]: Creating NEW OpenAI client instance")
            print(f"DEBUG [VibeProxy {timestamp}]: Endpoint: {base_url}")
            print(f"DEBUG [VibeProxy {timestamp}]: Token in use (first 20 chars): {api_key[:20] if api_key else 'None'}...")

            print(f"DEBUG [VibeProxy {timestamp}]: Custom headers: {custom_headers}")
            
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
        import time
        timestamp = time.strftime("%H:%M:%S")
        
        # Check for exact model matches first
        if self.big_client and config and model == config.big_model:
            print(f"DEBUG [Client Selection {timestamp}]: Using BIG client for model '{model}'")
            return self.big_client
        if self.middle_client and config and model == config.middle_model:
            print(f"DEBUG [Client Selection {timestamp}]: Using MIDDLE client for model '{model}'")
            return self.middle_client
        if self.small_client and config and model == config.small_model:
            print(f"DEBUG [Client Selection {timestamp}]: Using SMALL client for model '{model}'")
            return self.small_client

        # Fallback to default client
        print(f"DEBUG [Client Selection {timestamp}]: Using DEFAULT (cached) client for model '{model}'")
        print(f"DEBUG [Client Selection {timestamp}]: ⚠️  This client was created once and is being REUSED")
        return self.client
    
    async def create_chat_completion(self, request: Dict[str, Any], request_id: Optional[str] = None, config=None, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Send chat completion to OpenAI API with cancellation support.

        Args:
            request: OpenAI request dictionary
            request_id: Optional request ID for cancellation tracking
            config: Optional config object
            api_key: Optional per-request API key (for passthrough mode)
        """
        import time
        timestamp = time.strftime("%H:%M:%S")
        


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
            
            # FIX: For VibeProxy requests, ensure we have a fresh token for each request
            base_url = config.openai_base_url if config else self.default_base_url
            is_vibeproxy = "127.0.0.1:8317" in base_url or "localhost:8317" in base_url
            if is_vibeproxy:
                print(f"DEBUG [VibeProxy {timestamp}]: Refreshing client with fresh Antigravity token for request")
                from src.services.antigravity import get_antigravity_auth
                
                # Force refresh token from database
                auth = get_antigravity_auth()
                fresh_token = auth.get_token(force_refresh=True)
                
                if fresh_token:
                    print(f"DEBUG [VibeProxy {timestamp}]: Creating new client with fresh token (first 20 chars): {fresh_token[:20]}...")
                    # Create a fresh client with the new token
                    client = self._create_client(
                        fresh_token,
                        base_url,
                        config.azure_api_version if config else self.default_api_version,
                        self.custom_headers
                    )
                else:
                    print(f"ERROR [VibeProxy {timestamp}]: Failed to retrieve fresh token! Using cached client (may fail)")

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
        import time
        timestamp = time.strftime("%H:%M:%S")
        


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
            
            # FIX: For VibeProxy requests, ensure we have a fresh token for each request
            base_url = config.openai_base_url if config else self.default_base_url
            is_vibeproxy = "127.0.0.1:8317" in base_url or "localhost:8317" in base_url
            if is_vibeproxy:
                print(f"DEBUG [VibeProxy {timestamp}]: Refreshing client with fresh Antigravity token for streaming request")
                from src.services.antigravity import get_antigravity_auth
                
                # Force refresh token from database
                auth = get_antigravity_auth()
                fresh_token = auth.get_token(force_refresh=True)
                
                if fresh_token:
                    print(f"DEBUG [VibeProxy {timestamp}]: Creating new client with fresh token (first 20 chars): {fresh_token[:20]}...")
                    # Create a fresh client with the new token
                    client = self._create_client(
                        fresh_token,
                        base_url,
                        config.azure_api_version if config else self.default_api_version,
                        self.custom_headers
                    )
                else:
                    print(f"ERROR [VibeProxy {timestamp}]: Failed to retrieve fresh token! Using cached client (may fail)")

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

        # VibeProxy/Gemini-specific errors
        if "gemini code assist license" in error_str or "subscription_required" in error_str:
            return "Gemini Code Assist license required. Your Google Cloud Project needs a Gemini Code Assist license. Contact your administrator or use a different model/provider."
        
        if "auth_unavailable" in error_str or "no auth available" in error_str:
            return "VibeProxy authentication unavailable. Please ensure Antigravity IDE is running and you're logged in. Try restarting Antigravity IDE."
        
        if "permission_denied" in error_str and ("googleapis" in error_str or "cloudaicompanion" in error_str):
            return "Google Cloud permission denied. Check your Gemini/Antigravity credentials and project permissions."

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
    
    async def create_chat_completion_with_cascade(
        self,
        request: Dict[str, Any],
        tier: str,
        config=None,
        request_id: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Chat completion with cascade fallback on provider errors.
        
        Args:
            request: OpenAI request dictionary
            tier: Model tier (big, middle, small)
            config: Config object with cascade settings
            request_id: Optional request ID for cancellation
            api_key: Optional per-request API key
        
        Returns:
            ChatCompletion from first successful model
        """
        import ssl
        import httpx
        import time
        
        if not config or not config.model_cascade:
            # Cascade disabled - use normal call
            return await self.create_chat_completion(request, request_id, config, api_key)
        
        # Build models to try: primary + cascade
        primary_model = request.get("model", "")
        cascade_models = config.get_cascade_for_tier(tier)
        models_to_try = [primary_model] + cascade_models
        
        timestamp = time.strftime("%H:%M:%S")
        last_error = None
        
        # Track retry counts per model for soft failures
        retry_counts = {}
        MAX_RETRIES_BEFORE_CASCADE = 5  # Soft errors need 5 failures
        
        model_idx = 0
        while model_idx < len(models_to_try):
            model = models_to_try[model_idx]
            if not model:
                model_idx += 1
                continue
            
            # Initialize retry count for this model
            if model not in retry_counts:
                retry_counts[model] = 0
                
            try:
                # Update request with current model
                current_request = {**request, "model": model}
                
                if model_idx > 0 and retry_counts[model] == 0:
                    print(f"[CASCADE {timestamp}] ⚡ Trying fallback model: {model}")
                
                result = await self.create_chat_completion(current_request, request_id, config, api_key)
                
                if model_idx > 0:
                    print(f"[CASCADE {timestamp}] ✅ Success with fallback: {model}")
                
                return result
                
            except (ssl.SSLCertVerificationError, ssl.SSLError) as e:
                # SSL/Cert errors: switch IMMEDIATELY (hard failure)
                print(f"[CASCADE {timestamp}] 🔒 SSL/Cert error on {model} - switching immediately: {e}")
                last_error = e
                model_idx += 1  # Move to next model immediately
                continue
                
            except httpx.ConnectError as e:
                retry_counts[model] += 1
                print(f"[CASCADE {timestamp}] ⚠️  Connection error on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE}): {e}")
                last_error = e
                if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                    print(f"[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next")
                    model_idx += 1
                continue
                
            except httpx.TimeoutException as e:
                retry_counts[model] += 1
                print(f"[CASCADE {timestamp}] ⚠️  Timeout on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE}): {e}")
                last_error = e
                if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                    print(f"[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next")
                    model_idx += 1
                continue
                
            except RateLimitError as e:
                retry_counts[model] += 1
                print(f"[CASCADE {timestamp}] ⚠️  Rate limit on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE}): {e}")
                last_error = e
                if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                    print(f"[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next")
                    model_idx += 1
                # Add small delay on rate limit
                await asyncio.sleep(1)
                continue
            
            except (BadRequestError, AuthenticationError) as e:
                # 400/401 errors: switch IMMEDIATELY (model not available or auth failed)
                print(f"[CASCADE {timestamp}] 🚫 Request error on {model} - switching immediately: {e}")
                last_error = e
                model_idx += 1  # Move to next model immediately
                continue
                
            except APIError as e:
                # 502, 503, 504: retry with count
                if hasattr(e, 'status_code') and e.status_code in [502, 503, 504]:
                    retry_counts[model] += 1
                    print(f"[CASCADE {timestamp}] ⚠️  Server error {e.status_code} on {model} ({retry_counts[model]}/{MAX_RETRIES_BEFORE_CASCADE})")
                    last_error = e
                    if retry_counts[model] >= MAX_RETRIES_BEFORE_CASCADE:
                        print(f"[CASCADE {timestamp}] 🔄 Max retries reached for {model}, switching to next")
                        model_idx += 1
                    continue
                # Other API errors should not cascade
                raise
        
        # All models failed
        print(f"[CASCADE {timestamp}] ❌ All cascade models exhausted")
        if last_error:
            raise last_error
        raise APIError("All cascade models failed")