"""
SEO Quality Scoring System

Evaluates the SEO quality of generated product content based on professional
e-commerce SEO best practices.

Scoring Model:
- All categories equally weighted at 20 points each (6 categories = 120 total)
- Each category scored internally as 0-100%, then converted to 0-20 points
- Overall score = (total points / 120) × 100 = true percentage (0-100%)
"""

import re
from typing import Dict, List, Tuple
from models.schemas import ContentPackage

# Constants
POINTS_PER_CATEGORY = 20
NUM_CATEGORIES = 6
TOTAL_POSSIBLE_POINTS = POINTS_PER_CATEGORY * NUM_CATEGORIES  # 120


def calculate_seo_score(content_package: ContentPackage) -> Dict:
    """
    Calculate comprehensive SEO quality score for product content.

    All categories are equally weighted at 20 points each.
    Overall score is calculated as a true percentage (0-100%).

    Returns a dict with:
    - overall_score: 0-100% (true percentage)
    - category_scores: dict of point scores (0-20 each)
    - category_percentages: dict of percentage scores (0-100% each)
    - issues: list of identified issues
    - recommendations: list of improvement suggestions
    """

    issues = []
    recommendations = []

    # Calculate each category as percentage (0-100%)
    # 1. SEO Title
    title_pct, title_issues, title_recs = score_seo_title(
        content_package.titles_descriptions.seo_title,
        content_package.attributes.brand.value,
        content_package.seo_keywords.primary
    )
    issues.extend(title_issues)
    recommendations.extend(title_recs)

    # 2. Long Description
    desc_pct, desc_issues, desc_recs = score_long_description(
        content_package.titles_descriptions.long_description,
        content_package.attributes.brand.value
    )
    issues.extend(desc_issues)
    recommendations.extend(desc_recs)

    # 3. Keywords
    kw_pct, kw_issues, kw_recs = score_keywords(
        content_package.seo_keywords,
        content_package.attributes.brand.value
    )
    issues.extend(kw_issues)
    recommendations.extend(kw_recs)

    # 4. Brand Recognition
    brand_pct, brand_issues, brand_recs = score_brand_presence(
        content_package.titles_descriptions.seo_title,
        content_package.titles_descriptions.long_description,
        content_package.attributes.brand.value,
        content_package.seo_keywords.primary
    )
    issues.extend(brand_issues)
    recommendations.extend(brand_recs)

    # 5. Completeness
    complete_pct, complete_issues, complete_recs = score_completeness(
        content_package.attributes
    )
    issues.extend(complete_issues)
    recommendations.extend(complete_recs)

    # 6. Feature Highlights
    features_pct, features_issues, features_recs = score_feature_highlights(
        content_package.feature_highlights,
        content_package.attributes.brand.value
    )
    issues.extend(features_issues)
    recommendations.extend(features_recs)

    # Convert percentages to 20-point scale
    title_score = (title_pct / 100) * POINTS_PER_CATEGORY
    desc_score = (desc_pct / 100) * POINTS_PER_CATEGORY
    kw_score = (kw_pct / 100) * POINTS_PER_CATEGORY
    brand_score = (brand_pct / 100) * POINTS_PER_CATEGORY
    complete_score = (complete_pct / 100) * POINTS_PER_CATEGORY
    features_score = (features_pct / 100) * POINTS_PER_CATEGORY

    # Calculate overall score as percentage
    total_points = (
        title_score + desc_score + kw_score +
        brand_score + complete_score + features_score
    )
    overall_percentage = (total_points / TOTAL_POSSIBLE_POINTS) * 100

    # Determine grade based on percentage
    if overall_percentage >= 90:
        grade = "A"
        grade_label = "Excellent"
    elif overall_percentage >= 80:
        grade = "B+"
        grade_label = "Very Good"
    elif overall_percentage >= 70:
        grade = "B"
        grade_label = "Good"
    elif overall_percentage >= 60:
        grade = "C"
        grade_label = "Fair - Needs Improvement"
    else:
        grade = "D"
        grade_label = "Poor - Requires Revision"

    return {
        "overall_score": round(overall_percentage, 1),  # 0-100%
        "grade": grade,
        "grade_label": grade_label,
        "category_scores": {
            "seo_title": round(title_score, 1),
            "long_description": round(desc_score, 1),
            "keywords": round(kw_score, 1),
            "brand_presence": round(brand_score, 1),
            "completeness": round(complete_score, 1),
            "feature_highlights": round(features_score, 1)
        },
        "category_percentages": {
            "seo_title": round(title_pct, 1),
            "long_description": round(desc_pct, 1),
            "keywords": round(kw_pct, 1),
            "brand_presence": round(brand_pct, 1),
            "completeness": round(complete_pct, 1),
            "feature_highlights": round(features_pct, 1)
        },
        "category_max_points": POINTS_PER_CATEGORY,  # 20 for all
        "total_possible_points": TOTAL_POSSIBLE_POINTS,  # 120
        "issues": issues,
        "recommendations": recommendations
    }


def score_seo_title(title: str, brand: str, primary_keywords: List[str]) -> Tuple[float, List[str], List[str]]:
    """Score SEO title quality (returns 0-100%)"""
    score = 100.0
    issues = []
    recommendations = []

    # Check length (optimal: 60-70 chars)
    title_len = len(title)
    if title_len < 50:
        score -= 15
        issues.append(f"SEO title too short ({title_len} chars - recommended: 60-70 characters)")
        recommendations.append("Expand title to include more descriptive keywords")
    elif title_len > 75:
        score -= 10
        issues.append(f"SEO title too long ({title_len} chars - may be truncated in search results)")
        recommendations.append("Shorten title to 60-70 characters for better display")

    # Check for brand/character presence
    if brand and brand.lower() not in title.lower():
        score -= 25
        issues.append(f"Brand/franchise '{brand}' missing from SEO title")
        recommendations.append(f"Include '{brand}' at the beginning of the title")

    # Check for primary keywords
    keywords_in_title = sum(1 for kw in primary_keywords[:3] if kw.lower() in title.lower())
    if keywords_in_title == 0:
        score -= 20
        issues.append("No primary keywords found in SEO title")
        recommendations.append("Include at least 2-3 primary keywords in the title")
    elif keywords_in_title == 1:
        score -= 10
        issues.append("Only 1 primary keyword in title - should include 2-3")

    # Check for negative phrases
    negative_phrases = ["prison", "jail", "police", "handcuffs", "arrest"]
    if any(phrase in title.lower() for phrase in negative_phrases):
        score -= 15
        issues.append("Title contains negative phrase that may hurt conversion")
        recommendations.append("Reframe negative phrases with neutral or positive language")

    # Check for generic terms
    generic_terms = ["product", "item", "thing", "object"]
    if any(term in title.lower() for term in generic_terms):
        score -= 10
        issues.append("Title uses generic terms - be more specific")
        recommendations.append("Replace generic terms with specific product descriptors")

    return max(0, score), issues, recommendations


def score_long_description(description: str, brand: str) -> Tuple[float, List[str], List[str]]:
    """Score long description quality (returns 0-100%)"""
    score = 100.0
    issues = []
    recommendations = []

    word_count = len(description.split())
    sentence_count = len([s for s in description.split('.') if s.strip()])

    # Check word count (optimal: 200-350 words, minimum: 150)
    if word_count < 100:
        score -= 40
        issues.append(f"Description too short ({word_count} words - recommended: 200-350 words)")
        recommendations.append("Expand description to 200-350 words with details about features, benefits, uses")
    elif word_count < 150:
        score -= 20
        issues.append(f"Description below recommended length ({word_count} words - recommended: 200-350 words)")
        recommendations.append("Add more detail about materials, sizing, use cases, and emotional benefits")
    elif word_count < 200:
        score -= 8
        issues.append(f"Description slightly short ({word_count} words - recommended: 200-350 words)")
        recommendations.append("Expand to 200-350 words for optimal SEO impact")
    elif word_count > 400:
        score -= 8
        issues.append(f"Description may be too long ({word_count} words - recommended: 200-350 words)")
        recommendations.append("Consider condensing to 200-350 words for better readability")

    # Check sentence count (should be 8-12)
    if sentence_count < 6:
        score -= 12
        issues.append(f"Too few sentences ({sentence_count}) - should be 8-12 for proper structure")
        recommendations.append("Break content into more sentences for better flow")

    # Check for brand in first sentence
    first_sentence = description.split('.')[0] if '.' in description else description
    if brand and brand.lower() not in first_sentence.lower():
        score -= 16
        issues.append(f"Brand '{brand}' not mentioned in first sentence")
        recommendations.append(f"Start description with brand/franchise name for SEO impact")

    # Check for power words
    power_words = ["authentic", "premium", "perfect", "ideal", "must-have", "beloved", "iconic", "exclusive", "professional", "durable"]
    power_words_found = sum(1 for word in power_words if word in description.lower())
    if power_words_found < 2:
        score -= 12
        issues.append("Few emotional/power words - description needs more engaging language")
        recommendations.append("Add power words like 'authentic', 'premium', 'perfect', 'iconic' to increase appeal")

    # Check for specifications/dimensions
    spec_indicators = ["size", "inch", "cm", "tall", "wide", "compact", "large", "small", "dimension"]
    has_specs = any(indicator in description.lower() for indicator in spec_indicators)
    if not has_specs:
        score -= 12
        issues.append("No size/dimension information in description")
        recommendations.append("Include product dimensions or size descriptors")

    # Check for passive voice (basic check)
    passive_indicators = [" is ", " was ", " are ", " were ", " been "]
    passive_count = sum(description.lower().count(indicator) for indicator in passive_indicators)
    if passive_count > word_count * 0.08:  # More than 8% passive
        score -= 8
        issues.append("Too much passive voice - use active voice for more engaging copy")
        recommendations.append("Rewrite passive sentences to active voice")

    return max(0, score), issues, recommendations


def score_keywords(seo_keywords, brand: str) -> Tuple[float, List[str], List[str]]:
    """Score keyword quality (returns 0-100%)"""
    score = 100.0
    issues = []
    recommendations = []

    primary_count = len(seo_keywords.primary)
    long_tail_count = len(seo_keywords.long_tail)

    # Check primary keyword count (optimal: 8-12)
    if primary_count < 6:
        score -= 20
        issues.append(f"Too few primary keywords ({primary_count}) - should have 8-12")
        recommendations.append("Add more relevant primary keywords")
    elif primary_count > 15:
        score -= 10
        issues.append(f"Too many primary keywords ({primary_count}) - focus on 8-12 most relevant")
        recommendations.append("Reduce to 8-12 most impactful keywords")

    # Check long-tail keyword count (optimal: 5-8)
    if long_tail_count < 4:
        score -= 20
        issues.append(f"Too few long-tail keywords ({long_tail_count}) - should have 5-8")
        recommendations.append("Add long-tail phrases targeting specific search intents")
    elif long_tail_count > 10:
        score -= 5
        issues.append(f"Too many long-tail keywords ({long_tail_count}) - focus on 5-8 best phrases")

    # Check if brand is in primary keywords
    if brand:
        brand_in_primary = any(brand.lower() in kw.lower() for kw in seo_keywords.primary)
        if not brand_in_primary:
            score -= 25
            issues.append(f"Brand '{brand}' missing from primary keywords")
            recommendations.append(f"Add '{brand}' to primary keywords")

        # Check if brand is in long-tail
        brand_in_longtail = any(brand.lower() in phrase.lower() for phrase in seo_keywords.long_tail)
        if not brand_in_longtail:
            score -= 15
            issues.append(f"Brand '{brand}' not used in long-tail phrases")
            recommendations.append(f"Include '{brand}' in at least 2-3 long-tail phrases")

    # Check for generic keywords
    generic = ["product", "item", "thing", "stuff", "object"]
    generic_found = [kw for kw in seo_keywords.primary if kw.lower() in generic]
    if generic_found:
        score -= 15
        issues.append(f"Generic keywords found: {', '.join(generic_found)}")
        recommendations.append("Replace generic keywords with specific, descriptive terms")

    return max(0, score), issues, recommendations


def score_brand_presence(title: str, description: str, brand: str, keywords: List[str]) -> Tuple[float, List[str], List[str]]:
    """Score brand/franchise presence across content (returns 0-100%)"""
    score = 100.0
    issues = []
    recommendations = []

    if not brand or brand.lower() in ['n/a', 'none', 'generic', 'unknown']:
        # No brand detected - this is OK for generic products!
        # Give full score - don't penalize generic/unbranded products
        return 100.0, [], []

    brand_lower = brand.lower()

    # Check presence in title
    if brand_lower not in title.lower():
        score -= 33
        issues.append(f"Brand '{brand}' not in SEO title")
        recommendations.append(f"Add '{brand}' to beginning of title")

    # Check presence in description
    if brand_lower not in description.lower():
        score -= 27
        issues.append(f"Brand '{brand}' not mentioned in description")
        recommendations.append(f"Mention '{brand}' in first sentence of description")
    else:
        # Check if in first sentence
        first_sentence = description.split('.')[0] if '.' in description else description
        if brand_lower not in first_sentence.lower():
            score -= 13
            issues.append(f"Brand '{brand}' not in first sentence")
            recommendations.append("Move brand mention to opening sentence for better SEO")

    # Check presence in keywords
    if not any(brand_lower in kw.lower() for kw in keywords):
        score -= 27
        issues.append(f"Brand '{brand}' not in primary keywords")
        recommendations.append(f"Add '{brand}' as a primary keyword")

    return max(0, score), issues, recommendations


def score_completeness(attributes) -> Tuple[float, List[str], List[str]]:
    """Score attribute completeness (returns 0-100%)"""
    score = 100.0
    issues = []
    recommendations = []

    critical_attrs = ['material', 'color', 'size']  # Removed 'brand' - it's optional for generic products
    missing_critical = [attr for attr in critical_attrs if not getattr(attributes, attr).value]

    # Check if brand exists and is not generic
    brand_val = getattr(attributes, 'brand').value
    if brand_val and brand_val.lower() not in ['n/a', 'none', 'generic', 'unknown']:
        # If a brand is detected, it should be used properly (checked in brand_presence scoring)
        pass
    # If no brand or generic, that's perfectly fine - no penalty

    if missing_critical:
        penalty = len(missing_critical) * 25
        score -= penalty
        issues.append(f"Missing critical attributes: {', '.join(missing_critical)}")
        recommendations.append(f"Ensure these attributes are captured: {', '.join(missing_critical)}")

    # Check for low confidence on critical attributes (excluding brand for generic products)
    low_conf_critical = []
    for attr in critical_attrs:
        attr_val = getattr(attributes, attr)
        if attr_val.value and attr_val.confidence < 0.7:
            low_conf_critical.append(attr)

    if low_conf_critical:
        score -= len(low_conf_critical) * 10
        issues.append(f"Low confidence on critical attributes: {', '.join(low_conf_critical)}")
        recommendations.append("Verify and improve quality of source images for these attributes")

    return max(0, score), issues, recommendations


def score_feature_highlights(features: List[str], brand: str) -> Tuple[float, List[str], List[str]]:
    """Score feature highlights quality (returns 0-100%)"""
    score = 100.0
    issues = []
    recommendations = []

    feature_count = len(features)

    # Check count (optimal: 5-7)
    if feature_count < 4:
        score -= 30
        issues.append(f"Too few feature highlights ({feature_count}) - should have 5-7")
        recommendations.append("Add more specific feature benefits")
    elif feature_count > 8:
        score -= 10
        issues.append(f"Too many features ({feature_count}) - focus on 5-7 most important")

    # Check for brand mention in features
    if brand and not any(brand.lower() in f.lower() for f in features):
        score -= 20
        issues.append(f"Brand '{brand}' not mentioned in any feature highlight")
        recommendations.append(f"Include '{brand}' in at least one feature bullet")

    # Check for benefit-focused language
    benefit_words = ["perfect for", "ideal for", "great for", "ensures", "provides", "delivers", "authentic", "premium", "durable", "long-lasting"]
    benefit_count = sum(1 for f in features if any(word in f.lower() for word in benefit_words))

    if benefit_count < 2:
        score -= 30
        issues.append("Feature highlights lack benefit-focused language")
        recommendations.append("Rewrite features to emphasize benefits, not just specifications")

    # Check for generic features
    if any("feature" in f.lower() and "incomplete" in f.lower() for f in features):
        score -= 20
        issues.append("Generic/placeholder features detected")
        recommendations.append("Replace generic features with specific product benefits")

    return max(0, score), issues, recommendations
