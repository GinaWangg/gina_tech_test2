"""Base service for GPT and Gemini API calls.

This module provides the BaseService class that handles interactions with
Azure OpenAI GPT and Google Gemini APIs, mirroring the original implementation.
"""

import asyncio
import base64
import json
import time
from typing import Dict, List

from google import genai
from google.genai.types import Content, Part
from google.oauth2 import service_account
from openai import AsyncAzureOpenAI
from pydantic import BaseModel


class ResponseStruct(BaseModel):
    """Response structure for Gemini API."""

    kb_no: str
    answer: str


class BaseService:
    """Base service for GPT and Gemini API interactions.

    This service provides methods for calling Azure OpenAI GPT-4 and
    Google Gemini APIs with proper configuration and error handling.
    """

    def __init__(self, config: Dict):
        """Initialize base service with configuration.

        Args:
            config: Configuration dictionary containing API credentials
        """
        self.config = config

        # Azure OpenAI GPT-4.1 mini configuration
        self.model_gpt41_mini = config.get("TECH_OPENAI_GPT41MINI_PAYGO_EU_MODEL")
        self.openai_client_gpt41_mini = AsyncAzureOpenAI(
            azure_endpoint=config.get("TECH_OPENAI_GPT41MINI_PAYGO_EU_AZURE_ENDPOINT"),
            api_key=config.get("TECH_OPENAI_GPT41MINI_PAYGO_EU_API_KEY"),
            api_version=config.get("TECH_OPENAI_GPT41MINI_PAYGO_EU_API_VERSION"),
            timeout=30,
        )

        # Google Gemini (Vertex AI) configuration
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        info = json.loads(base64.b64decode(self.config.get("TECH_GEMINI_CREDENTIALS")))
        self.gemini_credentials = service_account.Credentials.from_service_account_info(
            info
        ).with_scopes(scopes)

        # Create GenAI client
        self.client = genai.Client(
            vertexai=True,
            project=self.gemini_credentials.project_id,
            location=config.get("TECH_GEMINI_LOCATION"),
            credentials=self.gemini_credentials,
        )
        self.model_name = config.get("TECH_GEMINI_MODEL_NAME")

    async def GPT41_mini_response(
        self, prompt: List[Dict], max_retries: int = 3
    ) -> str:
        """Get response from GPT-4.1 mini model.

        Args:
            prompt: List of message dictionaries with 'role' and 'content'
            max_retries: Maximum number of retry attempts

        Returns:
            Response text from GPT model
        """
        for attempt in range(max_retries):
            try:
                completion = (
                    await self.openai_client_gpt41_mini.chat.completions.create(
                        model=self.model_gpt41_mini,
                        messages=prompt,
                        temperature=0.7,
                        max_tokens=500,
                    )
                )
                return completion.choices[0].message.content.strip()
            except Exception:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)

    async def reply_gemini(
        self, user_input: str, max_retries: int = 3, retry_delay: float = 2.0
    ) -> Dict:
        """Get response from Gemini model.

        Args:
            user_input: User input text
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Dictionary containing response data
        """

        def _is_blank(x):
            return x is None or (isinstance(x, str) and x.strip() == "")

        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[Content(role="user", parts=[Part(text=user_input)])],
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": list[ResponseStruct],
                    },
                )

                resp0 = response.parsed[0]
                kb_no = (
                    resp0.get("kb_no")
                    if isinstance(resp0, dict)
                    else getattr(resp0, "kb_no", None)
                )
                answer = (
                    resp0.get("answer")
                    if isinstance(resp0, dict)
                    else getattr(resp0, "answer", None)
                )

                # Validate content: blank kb_no or answer triggers retry
                if _is_blank(kb_no) or _is_blank(answer):
                    raise ValueError("kb_no or answer is blank")

                return {
                    "response": resp0,
                    "exec_time": time.time() - start_time,
                }

            except Exception:
                if attempt == max_retries:
                    raise
                await asyncio.sleep(retry_delay)
