"""Ollama LLM client for text generation."""

import logging
from typing import List, Dict, Optional, AsyncGenerator

import ollama

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM."""

    def __init__(self, base_url: str, model: str):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL
            model: Model name to use for generation
        """
        self.base_url = base_url
        self.model = model
        self.client = ollama.Client(host=base_url)

    async def generate_response(
        self,
        prompt: str,
        context_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate a response using Ollama.


        """
        try:
            # Build messages for chat completion
            messages = []

            # Add conversation context if provided
            if context_messages:
                messages.extend(context_messages)

            # Add current prompt
            messages.append({
                "role": "user",
                "content": prompt
            })

            logger.info(f"Generating response with {len(messages)} messages using {self.model}")

            # Call Ollama chat API
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )

            generated_text = response['message']['content']
            logger.info(f"Generated response ({len(generated_text)} chars)")

            return generated_text

        except Exception as e:
            logger.error(f"Failed to generate response with Ollama: {e}")
            raise

    async def generate_response_stream(
        self,
        prompt: str,
        context_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using Ollama.

        Args:
            prompt: The prompt to send to the LLM
            context_messages: Optional conversation history
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Yields:
            Generated text chunks

        Raises:
            Exception: If generation fails
        """
        try:
            # Build messages for chat completion
            messages = []

            # Add conversation context if provided
            if context_messages:
                messages.extend(context_messages)

            # Add current prompt
            messages.append({
                "role": "user",
                "content": prompt
            })

            logger.info(f"Generating streaming response with {len(messages)} messages using {self.model}")

            # Call Ollama chat API with streaming
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )

            # Yield each chunk as it arrives
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    if content:
                        yield content

            logger.info("Streaming response completed")

        except Exception as e:
            logger.error(f"Failed to generate streaming response with Ollama: {e}")
            raise

    def check_model_availability(self) -> bool:
        """
        Check if the configured model is available.

        """
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models.get('models', [])]

            # Check if our model is in the list
            is_available = any(self.model in model for model in available_models)

            if is_available:
                logger.info(f"Model {self.model} is available")
            else:
                logger.warning(
                    f"Model {self.model} not found. Available models: {available_models}"
                )

            return is_available

        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
