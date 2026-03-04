from typing import Dict, List
from models.schemas import ContentPackage, QualityReport, HumanReviewFlag


def calculate_quality_report(
    content_package: ContentPackage,
    existing_flags: List[HumanReviewFlag]
) -> QualityReport:
    """Calculate comprehensive quality metrics for the content package."""

    human_review_flags = existing_flags.copy()
    image_quality_flags = []

    # Calculate attribute confidence scores
    attributes = content_package.attributes
    attr_confidences = {
        "material": attributes.material.confidence,
        "color": attributes.color.confidence,
        "style": attributes.style.confidence,
        "finish": attributes.finish.confidence,
        "target_demographic": attributes.target_demographic.confidence,
        "occasion": attributes.occasion.confidence
    }

    # Flag low confidence attributes
    for attr_name, confidence in attr_confidences.items():
        if confidence < 0.7:
            human_review_flags.append(HumanReviewFlag(
                field=f"attributes.{attr_name}",
                reason=f"Low confidence score: {confidence:.2f}"
            ))

    # Calculate section-level confidence
    confidence_by_section = {}

    # Attributes section: average of all attribute confidences
    confidence_by_section["attributes"] = sum(attr_confidences.values()) / len(attr_confidences)

    # Product identity: high confidence if not from defaults
    identity = content_package.product_identity
    if identity.category != "Uncategorized" and identity.marketing_tagline != "Product requires manual review":
        confidence_by_section["product_identity"] = 0.85
    else:
        confidence_by_section["product_identity"] = 0.5

    # Titles & Descriptions: high confidence if not default text
    titles = content_package.titles_descriptions
    if "Manual Review Required" not in titles.seo_title:
        confidence_by_section["titles_descriptions"] = 0.9
    else:
        confidence_by_section["titles_descriptions"] = 0.3

    # Feature highlights: based on count and quality
    features = content_package.feature_highlights
    if len(features) >= 5 and "manual review" not in features[0].lower():
        confidence_by_section["feature_highlights"] = 0.85
    elif len(features) >= 3:
        confidence_by_section["feature_highlights"] = 0.7
    else:
        confidence_by_section["feature_highlights"] = 0.5

    # SEO Keywords: based on count
    keywords = content_package.seo_keywords
    if len(keywords.primary) >= 8 and len(keywords.long_tail) >= 5:
        confidence_by_section["seo_keywords"] = 0.9
    elif len(keywords.primary) >= 5:
        confidence_by_section["seo_keywords"] = 0.75
    else:
        confidence_by_section["seo_keywords"] = 0.6

    # SKU Intelligence: based on completeness
    sku = content_package.sku_intelligence
    if sku.naming_suggestion != "PROD-UNKNOWN-000" and len(sku.variant_signals) > 0:
        confidence_by_section["sku_intelligence"] = 0.8
    else:
        confidence_by_section["sku_intelligence"] = 0.5

    # Count populated fields
    fields_total = 0
    fields_populated = 0

    # Product identity fields (4)
    fields_total += 4
    fields_populated += 1 if identity.category else 0
    fields_populated += 1 if identity.subcategory else 0
    fields_populated += 1 if identity.price_positioning else 0
    fields_populated += 1 if identity.marketing_tagline else 0

    # Titles & descriptions (3)
    fields_total += 3
    fields_populated += 1 if titles.seo_title else 0
    fields_populated += 1 if titles.short_description else 0
    fields_populated += 1 if titles.long_description else 0

    # Feature highlights (count as 1 field)
    fields_total += 1
    fields_populated += 1 if len(features) >= 3 else 0

    # Attributes (6)
    fields_total += 6
    fields_populated += 1 if attributes.material.value else 0
    fields_populated += 1 if attributes.color.value else 0
    fields_populated += 1 if attributes.style.value else 0
    fields_populated += 1 if attributes.finish.value else 0
    fields_populated += 1 if attributes.target_demographic.value else 0
    fields_populated += 1 if attributes.occasion.value else 0

    # SEO Keywords (2)
    fields_total += 2
    fields_populated += 1 if len(keywords.primary) > 0 else 0
    fields_populated += 1 if len(keywords.long_tail) > 0 else 0

    # SKU Intelligence (3)
    fields_total += 3
    fields_populated += 1 if sku.naming_suggestion else 0
    fields_populated += 1 if len(sku.variant_signals) > 0 else 0
    fields_populated += 1 if len(sku.bundle_pairings) > 0 else 0

    # Calculate completeness score (0-100)
    completeness_score = int((fields_populated / fields_total) * 100)

    # Add image quality flags based on common issues
    # These would be populated by VLM observations in a real implementation
    # For now, we'll leave this empty unless specific issues are detected

    return QualityReport(
        completeness_score=completeness_score,
        fields_populated=fields_populated,
        fields_total=fields_total,
        confidence_by_section=confidence_by_section,
        image_quality_flags=image_quality_flags,
        human_review_flags=human_review_flags
    )
