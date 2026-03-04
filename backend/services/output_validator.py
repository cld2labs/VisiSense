import json
import re
from typing import Optional, Tuple
from models.schemas import ContentPackage, HumanReviewFlag


def extract_json_from_text(text: str) -> Optional[str]:
    """Extract JSON from text that might contain markdown code blocks or other content."""

    # Try to find JSON in markdown code blocks
    code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        return match.group(1)

    # Try to find raw JSON object
    json_pattern = r"\{.*\}"
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        return match.group(0)

    return None


def validate_and_parse_output(raw_output: str, override_validation: bool = False) -> Tuple[Optional[ContentPackage], list, Optional[dict]]:
    """
    Validate and parse VLM output into ContentPackage schema.
    Returns tuple of (ContentPackage or None, list of HumanReviewFlag, warning_dict or None)

    If override_validation is True, warnings are ignored and processing continues.
    """

    human_review_flags = []
    warning_data = None

    # Try to parse as JSON
    try:
        data = json.loads(raw_output)

        # Check if this is a warning response (non-product detected)
        # Only return warning if override is NOT enabled
        if data.get("warning") == "non_product_detected":
            if not override_validation:
                warning_data = {
                    "type": "non_product_detected",
                    "reason": data.get("reason", "This image may not be a typical retail product."),
                    "image_type": data.get("image_type", "unknown")
                }
                return None, human_review_flags, warning_data
            else:
                # Override is enabled but AI still returned warning format
                # This shouldn't happen with updated prompt, but handle gracefully
                # Return error instead of silently failing
                human_review_flags.append(HumanReviewFlag(
                    field="raw_output",
                    reason="AI returned warning format despite override_validation=True. The model may need to be prompted differently."
                ))
                return None, human_review_flags, None

        # Check if this is a legacy "not_a_product" error response
        if data.get("error") == "not_a_product":
            if not override_validation:
                warning_data = {
                    "type": "non_product_detected",
                    "reason": data.get("reason", "Image does not contain a retail product"),
                    "image_type": "unknown"
                }
                return None, human_review_flags, warning_data
            else:
                # Same as above - handle gracefully
                human_review_flags.append(HumanReviewFlag(
                    field="raw_output",
                    reason="AI returned error format despite override_validation=True"
                ))
                return None, human_review_flags, None

    except json.JSONDecodeError:
        # Try to extract JSON from text
        extracted_json = extract_json_from_text(raw_output)
        if extracted_json:
            try:
                data = json.loads(extracted_json)
            except json.JSONDecodeError:
                human_review_flags.append(HumanReviewFlag(
                    field="raw_output",
                    reason="Failed to parse JSON from VLM output after extraction attempt"
                ))
                return None, human_review_flags, None
        else:
            human_review_flags.append(HumanReviewFlag(
                field="raw_output",
                reason="VLM output is not valid JSON and no JSON could be extracted"
            ))
            return None, human_review_flags, None

    # Fill in missing fields with defaults
    try:
        # Ensure all required nested structures exist
        if "product_identity" not in data:
            data["product_identity"] = {
                "category": "Uncategorized",
                "subcategory": None,
                "price_positioning": "MID-MARKET",
                "marketing_tagline": "Product requires manual review"
            }
            human_review_flags.append(HumanReviewFlag(
                field="product_identity",
                reason="Missing product_identity section in VLM output"
            ))

        if "titles_descriptions" not in data:
            data["titles_descriptions"] = {
                "seo_title": "Product Title - Manual Review Required",
                "short_description": "Description not available from image analysis.",
                "long_description": "Detailed description not available from image analysis."
            }
            human_review_flags.append(HumanReviewFlag(
                field="titles_descriptions",
                reason="Missing titles_descriptions section in VLM output"
            ))

        if "feature_highlights" not in data:
            data["feature_highlights"] = ["Feature analysis incomplete - manual review required"]
            human_review_flags.append(HumanReviewFlag(
                field="feature_highlights",
                reason="Missing feature_highlights in VLM output"
            ))

        if "attributes" not in data:
            data["attributes"] = {
                "material": {"value": None, "confidence": 0.0},
                "color": {"value": None, "confidence": 0.0},
                "style": {"value": None, "confidence": 0.0},
                "finish": {"value": None, "confidence": 0.0},
                "target_demographic": {"value": None, "confidence": 0.0},
                "occasion": {"value": None, "confidence": 0.0},
                "size": {"value": None, "confidence": 0.0},
                "brand": {"value": None, "confidence": 0.0}
            }
            human_review_flags.append(HumanReviewFlag(
                field="attributes",
                reason="Missing attributes section in VLM output"
            ))
        else:
            # Ensure new attributes exist with defaults if missing
            if "size" not in data["attributes"]:
                data["attributes"]["size"] = {"value": None, "confidence": 0.0}
            if "brand" not in data["attributes"]:
                data["attributes"]["brand"] = {"value": None, "confidence": 0.0}

        if "seo_keywords" not in data:
            data["seo_keywords"] = {
                "primary": ["product"],
                "long_tail": ["product for sale"]
            }
            human_review_flags.append(HumanReviewFlag(
                field="seo_keywords",
                reason="Missing seo_keywords section in VLM output"
            ))

        if "sku_intelligence" not in data:
            data["sku_intelligence"] = {
                "naming_suggestion": "PROD-UNKNOWN-000",
                "variant_signals": [],
                "bundle_pairings": []
            }
            human_review_flags.append(HumanReviewFlag(
                field="sku_intelligence",
                reason="Missing sku_intelligence section in VLM output"
            ))

        # Validate with Pydantic
        content_package = ContentPackage(**data)
        return content_package, human_review_flags, None

    except Exception as e:
        human_review_flags.append(HumanReviewFlag(
            field="schema_validation",
            reason=f"Schema validation error: {str(e)}"
        ))
        return None, human_review_flags, None
