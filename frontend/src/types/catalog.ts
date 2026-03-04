export interface AttributeValue {
  value: string | null;
  confidence: number;
}

export interface ProductIdentity {
  category: string;
  subcategory: string | null;
  price_positioning: 'PREMIUM' | 'MID-MARKET' | 'VALUE';
  marketing_tagline: string;
}

export interface TitlesDescriptions {
  seo_title: string;
  short_description: string;
  long_description: string;
}

export interface Attributes {
  material: AttributeValue;
  color: AttributeValue;
  style: AttributeValue;
  finish: AttributeValue;
  target_demographic: AttributeValue;
  occasion: AttributeValue;
  size: AttributeValue;
  brand: AttributeValue;
}

export interface SEOKeywords {
  primary: string[];
  long_tail: string[];
}

export interface SKUIntelligence {
  naming_suggestion: string;
  variant_signals: string[];
  bundle_pairings: string[];
}

export interface ContentPackage {
  product_identity: ProductIdentity;
  titles_descriptions: TitlesDescriptions;
  feature_highlights: string[];
  attributes: Attributes;
  seo_keywords: SEOKeywords;
  sku_intelligence: SKUIntelligence;
}

export interface HumanReviewFlag {
  field: string;
  reason: string;
}

export interface QualityReport {
  completeness_score: number;
  fields_populated: number;
  fields_total: number;
  confidence_by_section: Record<string, number>;
  image_quality_flags: string[];
  human_review_flags: HumanReviewFlag[];
}

export interface SEOScore {
  overall_score: number;  // Now 0-100 percentage, not sum of points
  grade: string;
  grade_label: string;
  category_scores: Record<string, number>;  // Each 0-20 points
  category_percentages: Record<string, number>;  // Each 0-100%
  category_max_points: number;  // 20 for all categories
  total_possible_points: number;  // 120 total
  issues: string[];
  recommendations: string[];
}

export interface AnalyzeResponse {
  status: string;
  processing_time_seconds: number;
  model_used: string;
  image_count: number;
  session_id: string;
  suggested_questions: string[];
  content_package: ContentPackage;
  quality_report: QualityReport;
  seo_score: SEOScore;
}

export interface ProcessingStatus {
  step: 'loading' | 'analyzing' | 'generating' | 'scoring' | 'complete' | 'error';
  message: string;
}

export interface ValidationWarning {
  type: string;
  reason: string;
  image_type: string;
  suggestion: string;
}
