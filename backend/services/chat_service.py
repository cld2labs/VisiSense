import logging
import json
from typing import List, Dict, Optional
from config import settings
from services.vision_client import VisionClient
from services.prompt_engine import build_chat_prompt
from models.schemas import ChatMessage

logger = logging.getLogger(__name__)

vision_client = VisionClient()


def is_text_only_query(message: str) -> bool:
    """Determine if query can be answered with text data only."""
    text_only_keywords = [
        'seo', 'description', 'title', 'copy', 'marketing', 'write', 'generate',
        'create', 'compose', 'draft', 'content', 'keyword', 'optimize', 'tagline'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in text_only_keywords)


async def chat_with_image(
    image_bytes_list: List[bytes],
    message: str,
    history: List[ChatMessage],
    product_data: Optional[Dict] = None,
    model: str = None
) -> str:
    """
    Send a chat message about the product image(s) using configured vision provider.
    Returns the assistant's response.
    """

    system_prompt = build_chat_prompt(history, product_data)
    full_prompt = f"{system_prompt}\nUser: {message}\nAssistant:"

    try:
        if is_text_only_query(message) and product_data:
            logger.info("Using text-only API for content generation query")
            assistant_response = await vision_client.chat_completion(full_prompt)
        else:
            assistant_response = await vision_client.analyze(image_bytes_list, full_prompt)

        if not assistant_response:
            return "I apologize, but I was unable to generate a response. Please try rephrasing your question."

        return assistant_response.strip()

    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        return f"An error occurred while processing your message: {str(e)}"
