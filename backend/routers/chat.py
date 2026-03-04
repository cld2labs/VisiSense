import os
import time
from fastapi import APIRouter, HTTPException

from services.chat_service import chat_with_image
from services.session_store import session_store
from models.schemas import ChatRequest, ChatResponse, ChatMessage


router = APIRouter()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llava:7b")
CHAT_MAX_HISTORY_TURNS = int(os.getenv("CHAT_MAX_HISTORY_TURNS", "10"))


@router.post("/chat")
async def chat_about_product(request: ChatRequest):
    """
    Chat about a product image using session context.
    Returns assistant response.
    """
    start_time = time.time()

    # Validate session exists
    if not session_store.session_exists(request.session_id):
        raise HTTPException(
            status_code=404,
            detail="Session expired — please re-analyze your product image"
        )

    # Get images from session
    images = session_store.get_images(request.session_id)
    if not images:
        raise HTTPException(
            status_code=404,
            detail="Session images not found"
        )

    # Get product analysis data from session
    product_data = session_store.get_product_data(request.session_id)

    # Limit history to prevent context overflow
    limited_history = request.history[-CHAT_MAX_HISTORY_TURNS*2:] if len(request.history) > CHAT_MAX_HISTORY_TURNS*2 else request.history

    try:
        # Get response from chat service
        assistant_message = await chat_with_image(
            images,
            request.message,
            limited_history,
            product_data,
            DEFAULT_MODEL
        )

        # Build response
        processing_time = time.time() - start_time
        response = ChatResponse(
            status="success",
            session_id=request.session_id,
            message=ChatMessage(role="assistant", content=assistant_message),
            processing_time_seconds=round(processing_time, 2)
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing error: {str(e)}"
        )
