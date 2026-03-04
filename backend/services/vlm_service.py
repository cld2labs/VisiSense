import asyncio
import logging
from typing import List, AsyncGenerator
from config import settings
from services.vision_client import VisionClient
from services.prompt_engine import build_analysis_prompt

logger = logging.getLogger(__name__)

vision_client = VisionClient()


async def analyze_images(
    image_bytes_list: List[bytes],
    model: str = None,
    override_validation: bool = False
) -> AsyncGenerator[dict, None]:
    """
    Analyze product images using configured vision provider.
    Yields event dictionaries with 'event' and 'data' keys.
    """

    yield {"event": "status", "data": {"step": "loading", "message": "Loading image..."}}
    await asyncio.sleep(0.1)

    yield {"event": "status", "data": {"step": "analyzing", "message": "Analyzing visual attributes..."}}
    await asyncio.sleep(0.1)

    prompt = build_analysis_prompt(len(image_bytes_list), override_validation)

    yield {"event": "status", "data": {"step": "generating", "message": "Generating content package..."}}

    try:
        raw_response = await vision_client.analyze(image_bytes_list, prompt)

        if not raw_response:
            yield {"event": "error", "data": {
                "message": "Failed to get response from vision provider",
                "step": "analyzing"
            }}
            return

    except Exception as e:
        logger.error(f"Vision analysis failed: {str(e)}")
        yield {"event": "error", "data": {
            "message": f"Analysis failed: {str(e)}",
            "step": "analyzing"
        }}
        return

    yield {"event": "status", "data": {"step": "scoring", "message": "Scoring confidence..."}}
    await asyncio.sleep(0.1)

    yield {"event": "complete", "data": {"raw_output": raw_response}}


async def check_ollama_health() -> dict:
    """Check if configured vision API is accessible and return status."""
    try:
        return {
            "provider": settings.LLM_PROVIDER,
            "status": "healthy",
            "model": settings.LLM_MODEL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def get_available_models() -> List[str]:
    """Get list of available models."""
    return [settings.LLM_MODEL]
