from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field


class AttributeValue(BaseModel):
    value: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


class ProductIdentity(BaseModel):
    category: str
    subcategory: Optional[str] = None
    price_positioning: Literal["PREMIUM", "MID-MARKET", "VALUE"]
    marketing_tagline: str


class TitlesDescriptions(BaseModel):
    seo_title: str
    short_description: str
    long_description: str


class Attributes(BaseModel):
    material: AttributeValue
    color: AttributeValue
    style: AttributeValue
    finish: AttributeValue
    target_demographic: AttributeValue
    occasion: AttributeValue
    size: AttributeValue  # Dimensions, size descriptors (e.g., "3 inches tall", "compact", "large")
    brand: AttributeValue  # Brand name or franchise (e.g., "Despicable Me", "Nike", "LEGO")


class SEOKeywords(BaseModel):
    primary: List[str]
    long_tail: List[str]


class SKUIntelligence(BaseModel):
    naming_suggestion: str
    variant_signals: List[str]
    bundle_pairings: List[str]


class ContentPackage(BaseModel):
    product_identity: ProductIdentity
    titles_descriptions: TitlesDescriptions
    feature_highlights: List[str]
    attributes: Attributes
    seo_keywords: SEOKeywords
    sku_intelligence: SKUIntelligence


class HumanReviewFlag(BaseModel):
    field: str
    reason: str


class QualityReport(BaseModel):
    completeness_score: int = Field(..., ge=0, le=100)
    fields_populated: int
    fields_total: int
    confidence_by_section: Dict[str, float]
    image_quality_flags: List[str]
    human_review_flags: List[HumanReviewFlag]


class SEOScore(BaseModel):
    overall_score: float
    grade: str
    grade_label: str
    category_scores: Dict[str, float]
    issues: List[str]
    recommendations: List[str]


class AnalyzeResponse(BaseModel):
    status: str
    processing_time_seconds: float
    model_used: str
    image_count: int
    session_id: str
    suggested_questions: List[str]
    content_package: ContentPackage
    quality_report: QualityReport
    seo_score: SEOScore


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: List[ChatMessage]


class ChatResponse(BaseModel):
    status: str
    session_id: str
    message: ChatMessage
    processing_time_seconds: float
