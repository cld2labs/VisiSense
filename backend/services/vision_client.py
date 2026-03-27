import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List
from config import settings
from utils.image_utils import image_to_base64

logger = logging.getLogger(__name__)


class VisionClient:
    """Universal vision client supporting any OpenAI-compatible API."""

    def __init__(self):
        logger.info(f"Initializing VisionClient with provider: {settings.LLM_PROVIDER}, model: {settings.LLM_MODEL}")

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def analyze(self, images: List[bytes], prompt: str) -> str:
        """Analyze images using configured vision API provider."""
        images_base64 = []
        for img_bytes in images:
            base64_str, _ = image_to_base64(img_bytes)
            images_base64.append(base64_str)

        image_contents = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"}
            }
            for img in images_base64
        ]

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_contents
                ]
            }
        ]

        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.LLM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

        try:
            logger.info(f"Sending vision analysis request with {len(images)} image(s)")
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT, verify=settings.VERIFY_SSL) as client:
                response = await client.post(
                    f"{settings.LLM_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                logger.info(f"Vision analysis successful, response length: {len(content)}")
                return content

        except Exception as e:
            logger.error(f"Vision analysis failed: {str(e)}")
            raise Exception(f"Vision analysis failed: {str(e)}")

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def chat_completion(self, prompt: str) -> str:
        """Get chat completion from configured provider."""
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS
        }

        headers = {
            "Content-Type": "application/json"
        }

        if settings.LLM_API_KEY:
            headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

        try:
            logger.info("Sending chat completion request")
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT, verify=settings.VERIFY_SSL) as client:
                response = await client.post(
                    f"{settings.LLM_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]
                logger.info(f"Chat completion successful, response length: {len(content)}")
                return content

        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            raise Exception(f"Chat completion failed: {str(e)}")
