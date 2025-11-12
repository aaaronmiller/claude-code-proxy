"""
Crosstalk Orchestrator - Model-to-Model Conversation System
Based on Exchange-of-Thought (EoT) research with 4 paradigms:
- Memory: Store and retrieve insights
- Report: Models report findings to each other
- Relay: Chain communication through models
- Debate: Contradictory reasoning with confidence evaluation
"""

import asyncio
import uuid
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from src.core.config import config
from src.core.client import OpenAIClient
from src.utils.system_prompt_loader import get_model_system_prompt


class CrosstalkParadigm(Enum):
    """EoT communication paradigms."""
    MEMORY = "memory"
    REPORT = "report"
    RELAY = "relay"
    DEBATE = "debate"


@dataclass
class CrosstalkMessage:
    """A message in a crosstalk conversation."""
    speaker: str
    listener: str
    content: str
    iteration: int
    timestamp: float = field(default_factory=time.time)
    confidence: Optional[float] = None
    message_type: str = "regular"  # regular, report, summary, challenge


@dataclass
class CrosstalkSession:
    """Represents a complete crosstalk session."""
    session_id: str
    models: List[str]
    system_prompts: Dict[str, str]
    paradigm: CrosstalkParadigm
    iterations: int
    topic: str
    created_at: float = field(default_factory=time.time)
    status: str = "configured"  # configured, running, completed, error
    history: List[CrosstalkMessage] = field(default_factory=list)
    memory_store: Dict[str, List[str]] = field(default_factory=dict)
    current_iteration: int = 0


class CrosstalkOrchestrator:
    """Orchestrates model-to-model conversations using EoT paradigms."""

    def __init__(self, config_obj):
        self.config = config_obj
        self.active_sessions: Dict[str, CrosstalkSession] = {}
        self.openai_client = OpenAIClient(
            config_obj.openai_api_key,
            config_obj.openai_base_url,
            config_obj.request_timeout,
            api_version=config_obj.azure_api_version,
        )
        # Configure per-model clients for hybrid deployments
        self.openai_client.configure_per_model_clients(config_obj)

    async def setup_crosstalk(
        self,
        models: List[str],
        system_prompts: Optional[Dict[str, str]] = None,
        paradigm: str = "relay",
        iterations: int = 20,
        topic: str = ""
    ) -> str:
        """
        Setup a new crosstalk session.

        Args:
            models: List of model IDs (e.g., ["big", "small"])
            system_prompts: Dict of model -> system prompt or file path
            paradigm: Communication paradigm (memory|report|relay|debate)
            iterations: Number of conversation exchanges
            topic: Initial topic/message

        Returns:
            Session ID for the new crosstalk
        """
        session_id = str(uuid.uuid4())

        # Load system prompts if not provided
        if system_prompts is None:
            system_prompts = {}
            for model in models:
                prompt = get_model_system_prompt(model, self.config)
                if prompt:
                    system_prompts[model] = prompt

        session = CrosstalkSession(
            session_id=session_id,
            models=models,
            system_prompts=system_prompts,
            paradigm=CrosstalkParadigm(paradigm),
            iterations=iterations,
            topic=topic
        )

        self.active_sessions[session_id] = session
        return session_id

    async def execute_crosstalk(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Execute a configured crosstalk session.

        Args:
            session_id: Session ID from setup_crosstalk

        Returns:
            Complete conversation history
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        session.status = "running"

        try:
            if session.paradigm == CrosstalkParadigm.MEMORY:
                await self._execute_memory_paradigm(session)
            elif session.paradigm == CrosstalkParadigm.REPORT:
                await self._execute_report_paradigm(session)
            elif session.paradigm == CrosstalkParadigm.RELAY:
                await self._execute_relay_paradigm(session)
            elif session.paradigm == CrosstalkParadigm.DEBATE:
                await self._execute_debate_paradigm(session)

            session.status = "completed"

        except Exception as e:
            session.status = "error"
            raise RuntimeError(f"Crosstalk execution failed: {str(e)}")

        # Convert to return format
        return self._session_to_dict(session)

    async def _execute_memory_paradigm(self, session: CrosstalkSession):
        """Memory paradigm: Store and retrieve insights from other models."""
        models = session.models

        # Each model solves the problem and stores its reasoning
        for model in models:
            # Model analyzes topic independently
            prompt = f"""
            Analyze the following topic and provide your insights:
            {session.topic}

            Provide a detailed analysis with reasoning.
            """
            response = await self._call_model(model, prompt, session.system_prompts.get(model, ""))
            session.history.append(CrosstalkMessage(
                speaker=model,
                listener="memory",
                content=response,
                iteration=0,
                message_type="analysis"
            ))

            # Store in memory
            if model not in session.memory_store:
                session.memory_store[model] = []
            session.memory_store[model].append(response)

        # Second round: models review each other's insights
        for model in models:
            other_insights = []
            for other_model in models:
                if other_model != model and other_model in session.memory_store:
                    other_insights.extend(session.memory_store[other_model])

            if other_insights:
                prompt = f"""
                You previously analyzed: {session.topic}

                Here are insights from other models:
                {chr(10).join(other_insights)}

                Review these insights and provide your final analysis.
                """
                response = await self._call_model(model, prompt, session.system_prompts.get(model, ""))
                session.history.append(CrosstalkMessage(
                    speaker=model,
                    listener="memory",
                    content=response,
                    iteration=1,
                    message_type="synthesis"
                ))

    async def _execute_report_paradigm(self, session: CrosstalkSession):
        """Report paradigm: Sequential reporting between models."""
        current_speaker = 0

        for iteration in range(session.iterations):
            speaker = session.models[current_speaker]
            listener = session.models[(current_speaker + 1) % len(session.models)]

            # Build context from previous messages
            context = self._build_conversation_context(session, iteration)

            # Speaker reports to listener
            prompt = f"""
            Previous context:
            {context}

            Your turn to respond to the ongoing discussion about: {session.topic}
            """
            response = await self._call_model(speaker, prompt, session.system_prompts.get(speaker, ""))

            session.history.append(CrosstalkMessage(
                speaker=speaker,
                listener=listener,
                content=response,
                iteration=iteration,
                message_type="report"
            ))

            current_speaker = (current_speaker + 1) % len(session.models)

    async def _execute_relay_paradigm(self, session: CrosstalkSession):
        """Relay paradigm: Chain communication through all models."""
        for iteration in range(session.iterations):
            # Each model responds to the previous one's message
            for i, speaker in enumerate(session.models):
                listener = session.models[(i + 1) % len(session.models)]

                # Get last message or initial topic
                last_message = session.history[-1].content if session.history else session.topic

                prompt = f"""
                Previous message: {last_message}

                Continue the conversation about: {session.topic}
                """
                response = await self._call_model(speaker, prompt, session.system_prompts.get(speaker, ""))

                session.history.append(CrosstalkMessage(
                    speaker=speaker,
                    listener=listener,
                    content=response,
                    iteration=iteration,
                    message_type="relay"
                ))

    async def _execute_debate_paradigm(self, session: CrosstalkSession):
        """Debate paradigm: Contradictory reasoning with confidence evaluation."""
        # Pair up models for debate
        models = session.models

        if len(models) < 2:
            raise ValueError("Debate requires at least 2 models")

        # First round: each model states its position
        for i, model in enumerate(models):
            prompt = f"""
            Debate topic: {session.topic}

            State your position and initial reasoning. Be confident in your stance.
            """
            response = await self._call_model(model, prompt, session.system_prompts.get(model, ""))
            confidence = 0.8 + (i * 0.05)  # Simulated confidence

            session.history.append(CrosstalkMessage(
                speaker=model,
                listener="all",
                content=response,
                iteration=0,
                confidence=confidence,
                message_type="opening"
            ))

        # Debate rounds: challenge each other
        for iteration in range(1, session.iterations):
            for i, challenger in enumerate(models):
                opponent = models[(i + 1) % len(models)]

                # Get opponent's last statement
                opponent_statements = [
                    msg for msg in session.history
                    if msg.speaker == opponent and msg.iteration == iteration - 1
                ]
                if not opponent_statements:
                    continue

                opponent_statement = opponent_statements[0].content

                prompt = f"""
                Opponent's position:
                {opponent_statement}

                Challenge this position and defend your own view on: {session.topic}
                Provide counterarguments with evidence.
                """
                response = await self._call_model(challenger, prompt, session.system_prompts.get(challenger, ""))

                # Simulated confidence based on argument strength
                confidence = 0.7 + (iteration * 0.02)

                session.history.append(CrosstalkMessage(
                    speaker=challenger,
                    listener=opponent,
                    content=response,
                    iteration=iteration,
                    confidence=confidence,
                    message_type="challenge"
                ))

    async def _call_model(self, model: str, prompt: str, system_prompt: str = "") -> str:
        """Call a model with prompt and system prompt."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        # Determine which model to use based on model size
        model_id = self.config.big_model if model == "big" else \
                    self.config.middle_model if model == "middle" else \
                    self.config.small_model

        request = {
            "model": model_id,
            "messages": messages,
            "max_tokens": 2000,
        }

        try:
            response = await self.openai_client.create_chat_completion(request, config=self.config)

            # Extract response content with error handling
            if not response.get("choices"):
                raise RuntimeError(f"No choices in response from {model_id}")

            choice = response["choices"][0]

            if "message" not in choice:
                raise RuntimeError(f"No message in response from {model_id}")

            if "content" not in choice["message"]:
                raise RuntimeError(f"No content in response from {model_id}")

            content = choice["message"]["content"]

            if not content:
                raise RuntimeError(f"Empty response from {model_id}")

            return content

        except KeyError as e:
            raise RuntimeError(f"Malformed response from {model_id}: missing field {str(e)}")
        except (IndexError, TypeError) as e:
            raise RuntimeError(f"Invalid response structure from {model_id}: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to call {model_id}: {str(e)}")

    def _build_conversation_context(self, session: CrosstalkSession, max_iterations: int) -> str:
        """Build conversation context from history."""
        recent_messages = session.history[-10:]  # Last 10 messages
        context_parts = []

        for msg in recent_messages:
            if msg.iteration <= max_iterations:
                context_parts.append(f"{msg.speaker}: {msg.content}")

        return "\n\n".join(context_parts) if context_parts else session.topic

    def _session_to_dict(self, session: CrosstalkSession) -> List[Dict[str, Any]]:
        """Convert session to dictionary for API return."""
        return [
            {
                "speaker": msg.speaker,
                "listener": msg.listener,
                "content": msg.content,
                "iteration": msg.iteration,
                "timestamp": msg.timestamp,
                "confidence": msg.confidence,
                "message_type": msg.message_type
            }
            for msg in session.history
        ]

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a crosstalk session."""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}

        session = self.active_sessions[session_id]
        return {
            "session_id": session.session_id,
            "status": session.status,
            "models": session.models,
            "paradigm": session.paradigm.value,
            "iterations": session.iterations,
            "current_iteration": session.current_iteration,
            "message_count": len(session.history),
            "created_at": session.created_at
        }

    def delete_session(self, session_id: str) -> bool:
        """Delete a completed or errored session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False


# Global orchestrator instance
crosstalk_orchestrator = CrosstalkOrchestrator(config)