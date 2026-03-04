import time
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from config import settings
from utils.image_utils import process_upload_file
from services.vlm_service import analyze_images, check_ollama_health, get_available_models
from services.output_validator import validate_and_parse_output
from services.confidence_scorer import calculate_quality_report
from services.prompt_engine import generate_suggested_questions
from services.session_store import session_store
from services.seo_scorer import calculate_seo_score
from models.schemas import AnalyzeResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze")
async def analyze_product(
    images: List[UploadFile] = File(...),
    model: Optional[str] = Form(None),
    override_validation: Optional[bool] = Form(False)
):
    """
    Analyze product images and generate complete content package.
    Returns SSE stream with status updates and final result.

    Args:
        images: Product images to analyze
        model: Optional model override
        override_validation: If True, bypass non-product warnings and proceed with analysis
    """
    start_time = time.time()

    # Validate number of images
    if len(images) < 1:
        raise HTTPException(status_code=400, detail="At least one image is required")
    if len(images) > settings.MAX_IMAGES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_IMAGES_PER_REQUEST} images allowed per request"
        )

    model_name = model or settings.LLM_MODEL
    logger.info(f"Starting analysis with {len(images)} image(s) using model: {model_name}")

    try:
        # Process all uploaded files
        image_bytes_list = []
        for image_file in images:
            image_bytes, metadata = await process_upload_file(image_file, settings.MAX_IMAGE_SIZE_MB)
            image_bytes_list.append(image_bytes)

        # Create session for chat
        session_id = session_store.create_session(image_bytes_list)

        # Define SSE generator
        async def generate_events():
            try:
                # Stream analysis events with override flag
                raw_output = None
                async for event_dict in analyze_images(image_bytes_list, model_name, override_validation):
                    event_type = event_dict["event"]
                    event_data = event_dict["data"]

                    # Check if this is the complete event
                    if event_type == "complete":
                        raw_output = event_data.get("raw_output")
                        break
                    elif event_type == "error":
                        yield f"event: error\ndata: {json.dumps(event_data)}\n\n"
                        return
                    else:
                        # Yield status events
                        yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

                if not raw_output:
                    error_response = {
                        "status": "error",
                        "message": "Failed to get response from VLM"
                    }
                    yield f"event: error\ndata: {json.dumps(error_response)}\n\n"
                    return

                # Validate and parse output
                content_package, validation_flags, warning_data = validate_and_parse_output(raw_output, override_validation)

                # Handle warning (non-product detection) - soft warning
                if warning_data and not content_package:
                    logger.info(f"Non-product warning detected: {warning_data}")
                    warning_response = {
                        "type": warning_data["type"],
                        "reason": warning_data["reason"],
                        "image_type": warning_data["image_type"],
                        "suggestion": "If this is wall art, a print, poster, or similar retail product, you can continue with analysis."
                    }
                    yield f"event: warning\ndata: {json.dumps(warning_response)}\n\n"
                    return

                # Handle hard errors
                if not content_package:
                    logger.error(f"Failed to parse VLM output. Raw output: {raw_output[:500]}...")
                    logger.error(f"Validation flags: {[flag.dict() for flag in validation_flags]}")

                    # Check for content policy refusal (hard block)
                    refusal_keywords = ["i'm sorry", "i can't assist", "i cannot help", "against policy"]
                    is_refusal = any(keyword in raw_output.lower() for keyword in refusal_keywords) if raw_output else False

                    if is_refusal:
                        error_message = "Image analysis was blocked by content policy. The image may contain prohibited content, identifiable faces, or sensitive material."
                        error_type = "content_policy_block"
                        tips = [
                            "Crop to show only the product",
                            "Use product-only photos without people",
                            "Ensure lighting clearly shows the item"
                        ]
                    else:
                        error_message = "Failed to parse VLM output. The response format was invalid."
                        error_type = "parsing_error"
                        tips = []

                    error_response = {
                        "status": "error",
                        "error_type": error_type,
                        "message": error_message,
                        "tips": tips,
                        "flags": [flag.dict() for flag in validation_flags],
                        "raw_preview": raw_output[:300] if raw_output else None
                    }
                    yield f"event: error\ndata: {json.dumps(error_response)}\n\n"
                    return

                # Calculate quality report
                quality_report = calculate_quality_report(content_package, validation_flags)

                # Calculate SEO quality score
                seo_score = calculate_seo_score(content_package)

                # Generate suggested questions
                suggested_questions = generate_suggested_questions(
                    content_package.product_identity.category,
                    content_package.attributes.dict()
                )

                # Build final response
                processing_time = time.time() - start_time
                response = AnalyzeResponse(
                    status="success",
                    processing_time_seconds=round(processing_time, 2),
                    model_used=model_name,
                    image_count=len(image_bytes_list),
                    session_id=session_id,
                    suggested_questions=suggested_questions,
                    content_package=content_package,
                    quality_report=quality_report,
                    seo_score=seo_score
                )

                # Store product data in session for chat context
                session_store.update_product_data(session_id, {
                    "content_package": content_package.dict(),
                    "quality_report": quality_report.dict(),
                    "model_used": model_name,
                    "seo_score": seo_score
                })

                # Send complete event
                yield f"event: complete\ndata: {response.model_dump_json()}\n\n"

            except Exception as e:
                logger.error(f"Analysis error: {str(e)}", exc_info=True)
                error_response = {
                    "status": "error",
                    "message": f"Unexpected error: {str(e)}"
                }
                yield f"event: error\ndata: {json.dumps(error_response)}\n\n"

        return StreamingResponse(
            generate_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check health of the service and vision provider connectivity."""
    provider_status = await check_ollama_health()

    if provider_status["status"] == "unhealthy":
        return {
            "status": "degraded",
            "backend": "healthy",
            "vision_provider": provider_status
        }

    return {
        "status": "healthy",
        "backend": "healthy",
        "vision_provider": provider_status
    }


@router.get("/models")
async def list_models():
    """Get list of available models."""
    models = await get_available_models()
    return {
        "models": models,
        "default": settings.LLM_MODEL
    }


@router.post("/regenerate")
async def regenerate_section(
    session_id: str = Form(...),
    section: str = Form(...),
    user_instructions: str = Form(...)
):
    """
    Regenerate a specific section based on user feedback.

    Args:
        session_id: Session ID from original analysis
        section: Section to regenerate (e.g., "seo_content")
        user_instructions: User's feedback/requirements
    """
    # Get session data
    session_data = session_store.get_product_data(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    try:
        # Build regeneration prompt
        content_package = session_data.get("content_package", {})
        product_identity = content_package.get("product_identity", {})
        attributes = content_package.get("attributes", {})

        # Extract brand for SEO compliance
        brand = attributes.get('brand', {}).get('value', None)
        size = attributes.get('size', {}).get('value', None)

        regeneration_prompt = f"""You are a professional SEO copywriter regenerating product content based on user feedback.

CRITICAL PRODUCT DETAILS:
Category: {product_identity.get('category', 'Unknown')}
Subcategory: {product_identity.get('subcategory', 'N/A')}
Price Positioning: {product_identity.get('price_positioning', 'N/A')}

PRODUCT ATTRIBUTES:
Brand/Franchise: {brand or 'N/A'} ⚠️ MUST include in title if present!
Material: {attributes.get('material', {}).get('value', 'N/A')}
Color: {attributes.get('color', {}).get('value', 'N/A')}
Size: {size or 'N/A'}
Style: {attributes.get('style', {}).get('value', 'N/A')}
Target Demographic: {attributes.get('target_demographic', {}).get('value', 'N/A')}

USER FEEDBACK/REQUIREMENTS:
{user_instructions}

⚠️ CRITICAL WORD COUNT ALERT:
If the user mentions "short", "word count", "161 words", "200 words", or similar, they are telling you the current description is TOO SHORT.
You MUST create a description with AT LEAST 200 words to fix this issue.
This is the PRIMARY goal of this regeneration request!

SEO REQUIREMENTS (MANDATORY - DO NOT SKIP):
1. SEO title MUST be 60-70 characters
   - Include brand if present: "{brand or 'Product'} [Type] - [Key Feature]"

2. Short description MUST be 150-200 characters
   - 2-3 complete sentences
   - Include brand and key benefit

3. Long description MUST be 200-350 WORDS (NOT characters!)
   ⚠️ CRITICAL: Count your words! This is 10-12 sentences minimum.
   ⚠️ USER IS ASKING YOU TO FIX WORD COUNT - DO NOT output anything under 200 words!

   REQUIRED STRUCTURE (follow exactly - EACH POINT IS 1-2 SENTENCES):
   - Sentence 1-2: Hook with emotional appeal and product introduction (30-40 words)
   - Sentence 3-4: Visual features (color: {attributes.get('color', {}).get('value', 'N/A')}, style, design) (25-35 words)
   - Sentence 5-6: Material quality ({attributes.get('material', {}).get('value', 'N/A')}), durability, craftsmanship (30-40 words)
   - Sentence 7-8: Size details (mention "medium size" or specific dimensions), display context (25-35 words)
   - Sentence 9-10: Target audience, occasions, gifting ideas (30-40 words)
   - Sentence 11-12: Unique value proposition, emotional benefits, call-to-action (30-40 words)
   - OPTIONAL Sentence 13-14: Additional benefits, care instructions, or collectibility (20-30 words if needed to reach 200)

4. Use emotional, benefit-driven language throughout
5. NO negative phrases in the title (avoid "prison", "jail", etc.)

WORD COUNT VERIFICATION (MANDATORY):
- Before responding, COUNT the words in your long description
- Minimum 200 words REQUIRED - add more detail if below this
- If the user's instruction mentions "short" or "word count", you MUST generate 200+ words
- Target: 250-300 words for best SEO performance
- Add specific details about materials, uses, benefits, quality to reach word count

FINAL VERIFICATION BEFORE RESPONDING:
1. Count the words in your long_description (split by spaces)
2. If count is less than 200, GO BACK and add more sentences with specific details
3. Keep adding until you reach 200-350 words
4. Do NOT proceed until word count is verified to be 200+

Generate ONLY the titles and descriptions section incorporating user feedback AND all SEO requirements.
Respond with ONLY valid JSON in this exact format:
{{
  "seo_title": "60-70 character SEO optimized title with brand if present",
  "short_description": "2-3 sentences, 150-200 characters, engaging",
  "long_description": "MINIMUM 200 WORDS - Count before submitting! Add more sentences about features, benefits, quality, uses, target audience, emotional appeal, and brand story to reach this requirement. Be specific and detailed."
}}

REMEMBER: If the user instruction mentions "short" or "word count", they are explicitly asking you to fix this by making it LONGER (200+ words)!"""

        from services.vision_client import VisionClient
        vision_client = VisionClient()

        response_text = await vision_client.chat_completion(regeneration_prompt)

        # Parse response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            regenerated_data = json.loads(json_match.group(0))
        else:
            regenerated_data = json.loads(response_text)

        # Update session with new content
        content_package["titles_descriptions"] = regenerated_data

        # Recalculate SEO score with new content
        from services.seo_scorer import calculate_seo_score
        from models.schemas import ContentPackage

        # Store old score for improvement calculation
        old_seo_score = session_data.get("seo_score", {})
        old_score = old_seo_score.get("overall_score", 0) if old_seo_score else 0

        # Calculate new score
        updated_package = ContentPackage(**content_package)
        new_seo_score = calculate_seo_score(updated_package)

        # Update session with new content and score
        session_store.update_product_data(session_id, {
            "content_package": content_package,
            "quality_report": session_data.get("quality_report"),
            "model_used": session_data.get("model_used"),
            "seo_score": new_seo_score
        })

        return {
            "status": "success",
            "section": section,
            "updated_content": regenerated_data,
            "seo_score": new_seo_score,
            "improvement": round(new_seo_score['overall_score'] - old_score, 1)
        }

    except Exception as e:
        logger.error(f"Regeneration error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@router.post("/enhance-seo")
async def enhance_seo(
    session_id: str = Form(...)
):
    """
    Auto-enhance SEO content by fixing identified issues and applying recommendations.

    Args:
        session_id: Session ID from original analysis
    """
    # Get session data
    session_data = session_store.get_product_data(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    try:
        # Get current content and calculate SEO score to identify issues
        content_package = session_data.get("content_package", {})
        product_identity = content_package.get("product_identity", {})
        attributes = content_package.get("attributes", {})

        # Import here to avoid circular dependency
        from services.seo_scorer import calculate_seo_score
        from models.schemas import ContentPackage

        # Calculate current score
        current_package = ContentPackage(**content_package)
        seo_score = calculate_seo_score(current_package)

        # Extract brand for SEO compliance
        brand = attributes.get('brand', {}).get('value', None)
        size = attributes.get('size', {}).get('value', None)

        # Build comprehensive enhancement prompt
        enhancement_prompt = f"""You are a professional SEO specialist tasked with enhancing product content to achieve a 90+ SEO score.

PRODUCT DETAILS:
Category: {product_identity.get('category', 'Unknown')}
Subcategory: {product_identity.get('subcategory', 'N/A')}
Brand/Franchise: {brand or 'Generic'} ⚠️ CRITICAL - Include in title!
Material: {attributes.get('material', {}).get('value', 'N/A')}
Color: {attributes.get('color', {}).get('value', 'N/A')}
Size: {size or 'N/A'}
Style: {attributes.get('style', {}).get('value', 'N/A')}
Target Demographic: {attributes.get('target_demographic', {}).get('value', 'N/A')}
Price Positioning: {product_identity.get('price_positioning', 'N/A')}

CURRENT CONTENT (NEEDS IMPROVEMENT):
Title: {content_package.get('titles_descriptions', {}).get('seo_title', 'N/A')}
Short Desc: {content_package.get('titles_descriptions', {}).get('short_description', 'N/A')}
Long Desc: {content_package.get('titles_descriptions', {}).get('long_description', 'N/A')}

IDENTIFIED ISSUES TO FIX:
{chr(10).join('- ' + issue for issue in seo_score['issues'][:5])}

RECOMMENDATIONS TO APPLY:
{chr(10).join('- ' + rec for rec in seo_score['recommendations'][:5])}

YOUR TASK - Create SEO-optimized content that achieves 90+ score:

MANDATORY REQUIREMENTS:
1. SEO Title (60-70 chars):
   - Start with brand/character name if present: "{brand or 'Product'} [Type] - [Key Feature]"
   - Include primary benefit and use case
   - NO negative words (prison, jail, etc.)
   - Example: "Minion Character Figurine - Despicable Me Collectible Toy"

2. Short Description (150-200 chars):
   - Include brand name in first 3 words
   - Highlight unique value proposition
   - Use power words: authentic, premium, perfect, iconic
   - Example: "Authentic {brand or 'Product'} featuring [key features]. Perfect for [target audience]!"

3. Long Description MUST be 200-350 WORDS (NOT characters!):
   ⚠️ CRITICAL: Count your words carefully! Minimum 200 words REQUIRED.
   ⚠️ This is an ENHANCEMENT request - output MUST be 200+ words to fix SEO issues!

   STRUCTURE (follow exactly, 10-14 sentences with target word counts):
   - Sentence 1-2: Hook with emotional appeal and product introduction (30-40 words)
   - Sentence 3-4: Visual features (color: {attributes.get('color', {}).get('value', 'N/A')}, style, design details) (25-35 words)
   - Sentence 5-6: Material quality ({attributes.get('material', {}).get('value', 'N/A')}), durability, craftsmanship (30-40 words)
   - Sentence 7-8: Size details (mention size or dimensions), display/usage context (25-35 words)
   - Sentence 9-10: Target audience, occasions, perfect gifting scenarios (30-40 words)
   - Sentence 11-12: Unique value proposition, emotional benefits, call-to-action (30-40 words)
   - Sentence 13-14: Additional benefits, collectibility, care tips, or brand story (20-30 words to ensure 200+ total)

   WRITING STYLE:
   - Use active voice and power words
   - Include emotional triggers: beloved, iconic, must-have, delightful
   - Mention specifications naturally
   - Add trust signals: durable, high-quality, authentic, detailed
   - Create urgency: perfect gift, essential addition, don't miss

WORD COUNT VERIFICATION (MANDATORY):
- Before responding, COUNT the words in your long description
- Minimum 200 words ABSOLUTELY REQUIRED - no exceptions!
- If below 200 words, ADD more descriptive sentences with specific details
- Target: 250-300 words for optimal SEO performance
- Be detailed, specific, and comprehensive to reach the word count

FINAL VERIFICATION BEFORE RESPONDING:
1. Count the words in your long_description (split by spaces)
2. If count is less than 200, GO BACK and add more sentences
3. Add details about: craftsmanship, materials, display ideas, gift scenarios, brand heritage, emotional benefits
4. Keep adding until you reach 200-350 words
5. Do NOT proceed until word count is verified to be 200+

Respond with ONLY valid JSON in this exact format:
{{
  "seo_title": "60-70 character optimized title",
  "short_description": "150-200 character engaging description",
  "long_description": "MINIMUM 200 WORDS REQUIRED - Count before submitting! Be comprehensive and detailed about all product aspects to reach this requirement."
}}

CRITICAL: You are enhancing SEO - if word count is an issue, you MUST output 200+ words to fix it!"""

        from services.vision_client import VisionClient
        vision_client = VisionClient()

        response_text = await vision_client.chat_completion(enhancement_prompt)

        # Parse response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            enhanced_data = json.loads(json_match.group(0))
        else:
            enhanced_data = json.loads(response_text)

        # Update session with enhanced content
        content_package["titles_descriptions"] = enhanced_data

        # Recalculate SEO score with new content
        updated_package = ContentPackage(**content_package)
        new_seo_score = calculate_seo_score(updated_package)

        session_store.update_product_data(session_id, {
            "content_package": content_package,
            "quality_report": session_data.get("quality_report"),
            "model_used": session_data.get("model_used")
        })

        return {
            "status": "success",
            "updated_content": enhanced_data,
            "seo_score": new_seo_score,
            "improvement": round(new_seo_score['overall_score'] - seo_score['overall_score'], 1)
        }

    except Exception as e:
        logger.error(f"SEO enhancement error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")
