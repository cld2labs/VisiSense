from typing import List
from models.schemas import ChatMessage


def build_analysis_prompt(image_count: int, override_validation: bool = False) -> str:
    """Build the prompt for product analysis.

    Args:
        image_count: Number of images being analyzed
        override_validation: If True, skip validation and force analysis
    """

    base_prompt = """You are an expert retail merchandising specialist analyzing product images to generate comprehensive catalog content.

Your task is to analyze the provided product image(s) and extract detailed information to create a complete retail content package."""

    # Only add validation section if override is not enabled
    if not override_validation:
        base_prompt += """

IMPORTANT IMAGE VALIDATION:
First, determine if this image shows a PHYSICAL RETAIL PRODUCT (merchandise that can be sold).

If the image appears to be:
- A scenic view, landscape photo, or nature image (unless it's a photo print/poster product)
- An infographic, diagram, chart, or educational illustration (unless it's wall art/educational poster product)
- A screenshot, meme, or social media post
- Text-heavy content, presentations, or slides (unless it's a printed product)
- People without a clear product focus
- Abstract artwork or paintings without a physical product form

Then respond with ONLY this JSON:
{"warning": "non_product_detected", "reason": "This image appears to be [type], not a typical retail product. However, if this is wall art, a print, poster, or similar product meant for retail sale, analysis can proceed.", "image_type": "[infographic|scenic_photo|text_content|artwork|other]"}

NOTE: Wall art, prints, posters, educational materials, and decorative items ARE valid products. Only flag if you're uncertain about retail intent.

ONLY proceed with full analysis if the image clearly shows a PHYSICAL PRODUCT that could be sold in retail (e.g., toys, clothing, electronics, furniture, home goods, accessories, wall art, prints, etc.)."""
    else:
        base_prompt += """

ANALYSIS MODE: User has confirmed this should be analyzed as a retail product.
Proceed with full analysis treating this as merchandise meant for sale, even if it appears to be artwork, a diagram, or informational content.

DO NOT return any warning JSON or error responses. You MUST return the full product analysis in the OUTPUT SCHEMA format below.
Skip all validation checks - the user has explicitly requested analysis of this image as a product."""

    base_prompt += """

CRITICAL: You MUST respond ONLY with valid JSON. No markdown code blocks, no explanations, no additional text. Just pure JSON.

OUTPUT SCHEMA:
{
  "product_identity": {
    "category": "string (e.g., Home & Garden, Fashion, Electronics)",
    "subcategory": "string or null",
    "price_positioning": "PREMIUM" | "MID-MARKET" | "VALUE",
    "marketing_tagline": "string (compelling 8-15 word tagline)"
  },
  "titles_descriptions": {
    "seo_title": "string (60-70 chars, keyword-rich)",
    "short_description": "string (2-3 sentences, 150-200 chars)",
    "long_description": "string (8-12 sentences, 200-350 words, emotionally engaging, detailed, benefit-focused)"
  },
  "feature_highlights": [
    "string (bullet point)",
    "string (5-7 total)"
  ],
  "attributes": {
    "material": {"value": "string or null", "confidence": 0.0-1.0},
    "color": {"value": "string or null", "confidence": 0.0-1.0},
    "style": {"value": "string or null", "confidence": 0.0-1.0},
    "finish": {"value": "string or null", "confidence": 0.0-1.0},
    "target_demographic": {"value": "string or null", "confidence": 0.0-1.0},
    "occasion": {"value": "string or null", "confidence": 0.0-1.0},
    "size": {"value": "string or null (e.g., '3-inch tall', 'compact', 'large', 'palm-sized')", "confidence": 0.0-1.0},
    "brand": {"value": "string or null (brand/franchise name if recognizable: 'Despicable Me', 'Nike', 'LEGO')", "confidence": 0.0-1.0}
  },
  "seo_keywords": {
    "primary": ["keyword1", "keyword2", "..."],
    "long_tail": ["long tail phrase 1", "..."]
  },
  "sku_intelligence": {
    "naming_suggestion": "string (SKU format like PROD-CAT-COLOR-SIZE)",
    "variant_signals": ["color variant", "size variant", "..."],
    "bundle_pairings": ["complementary product 1", "..."]
  }
}

ANALYSIS RULES:

⚠️ CRITICAL SEO REQUIREMENTS (Your output will be scored 0-100%):
   Your analysis will be evaluated against these SEO quality criteria (20 points each, 120 total):

   1. SEO TITLE QUALITY (20 points):
      - Length: 60-70 characters (STRICT)
      - Contains brand/character name (if recognizable)
      - Includes 2-3 primary keywords
      - Clear, descriptive, benefit-focused

   2. LONG DESCRIPTION QUALITY (20 points):
      - Length: 200-350 words (STRICT - count carefully!)
      - Includes 3-5 primary keywords naturally
      - Well-structured (8-12 sentences)
      - Engaging, benefit-driven, detailed

   3. KEYWORD STRATEGY (20 points):
      - 8-12 primary keywords (EXACT count required)
      - 5-8 long-tail phrases (3-5 words each)
      - Brand/franchise terms included (if applicable)
      - Relevant, specific, search-optimized

   4. BRAND RECOGNITION (20 points):
      - Brand/character identified if visible
      - Included in title, description, keywords
      - Prominent and consistent throughout

   5. COMPLETENESS (20 points):
      - All required fields populated
      - No null/empty values where data available
      - Confidence scores provided
      - All sections detailed

   6. FEATURE HIGHLIGHTS QUALITY (20 points):
      - 5-7 bullet points (EXACT count)
      - Benefit-driven language
      - Specific and actionable
      - Well-written and compelling

   📊 OVERALL SCORE: (Total points / 120) × 100 = Percentage
   - 90-100% = A (Excellent)
   - 80-89% = B+ (Very Good)
   - 70-79% = B (Good)
   - 60-69% = C (Fair)
   - Below 60% = D (Poor)

   AIM FOR 85%+ by following ALL requirements precisely!

1. BASE OBSERVATIONS:
   - Base ALL observations on visual evidence only
   - Use null for value if attribute cannot be determined from image
   - Be specific and descriptive - avoid generic terms

2. CONFIDENCE SCORING:
   - 1.0: Absolutely certain from clear visual evidence
   - 0.9: Very confident, clearly visible
   - 0.8: Confident, reasonably clear
   - 0.7: Moderate confidence, some ambiguity
   - <0.7: Low confidence, unclear or inferred

3. BRAND & CHARACTER RECOGNITION (CRITICAL FOR SEO):
   If you recognize a licensed character, brand name, franchise, or well-known product (e.g., Minion/Despicable Me, Barbie, LEGO, Mickey Mouse/Disney, Star Wars, Marvel, Nike, Apple), you MUST:
   - Include BOTH character name AND franchise in SEO title: "Minion Character Figurine - Despicable Me Collectible" NOT "Yellow Figure Toy"
   - Add franchise/brand name to PRIMARY keywords (e.g., "Despicable Me", "Minion", "Illumination")
   - Mention franchise/brand in first sentence of long description
   - For licensed products, add "officially licensed" or "authentic" if logo/branding visible
   - Include franchise-specific keywords in long-tail phrases

4. SEO TITLE OPTIMIZATION (CRITICAL - MUST BE 60-70 CHARACTERS):
   REQUIREMENTS (Each missing element reduces SEO score):
   - Length: MUST be between 60-70 characters (aim for 65)
   - Brand/Character: Include at beginning if recognizable (Minion, Nike, LEGO, etc.)
   - Primary Keywords: Include 2-3 primary keywords naturally
   - Format: [Brand/Character] [Product Type] [Key Feature] [Use Case]

   Examples of GOOD titles (60-70 chars):
   - "Minion Character Figurine - Despicable Me Collectible Toy" (59 chars) ✓
   - "Nike Air Max Running Shoes - Breathable Athletic Sneakers" (58 chars) ✓
   - "Vintage Oak Coffee Table - Mid-Century Modern Living Room" (58 chars) ✓

   Examples of BAD titles:
   - "Yellow Figure Toy" (18 chars) ✗ TOO SHORT, no brand, no keywords
   - "Toy" (3 chars) ✗ TERRIBLE - way too short
   - "This is an amazing super incredible wonderful fantastic yellow character figurine collectible toy for children and adults to display" (134 chars) ✗ TOO LONG

   MUST include: Brand (if visible), primary benefit, target use case
   AVOID: Generic terms, negative phrases ("prison outfit"), passive voice, being too short

5. LONG DESCRIPTION RULES (CRITICAL - MUST BE 200-350 WORDS, 8-12 SENTENCES):
   LENGTH REQUIREMENT: MUST be between 200-350 words (aim for 250-300 words)
   - Too short (under 200 words) = MAJOR SEO penalty
   - Too long (over 350 words) = Minor penalty for being too verbose
   - Count your words carefully!

   KEYWORD REQUIREMENT: Include 3-5 primary keywords naturally throughout (no keyword stuffing)

   Structure (8-12 sentences):
   - Sentence 1: Hook with brand/character + emotional benefit
   - Sentences 2-3: Key features with sensory details (look, feel, function)
   - Sentences 4-5: Material, construction, quality, durability
   - Sentences 6-7: Size, dimensions, display/use context
   - Sentences 8-9: Target audience + occasions (gift, collection, personal use)
   - Sentences 10-11: Unique value proposition + emotional appeal
   - Sentence 12: Call-to-action or ownership statement

   Writing Style:
   - Use active, benefit-driven language ("brings joy", "transforms", "captures")
   - Include emotional triggers ("beloved", "iconic", "charming", "delightful")
   - Add trust signals when visible ("durable", "high-quality", "authentic", "detailed")
   - Mention specifications naturally ("compact size", "vibrant colors", "smooth finish")
   - Use power words: "must-have", "perfect", "ideal", "essential", "premium"
   - Avoid: Passive voice, repetition, filler words, generic phrases
   - IMPORTANT: Make it detailed and substantial - reach 200-350 word count!

6. SHORT DESCRIPTION (150-200 chars):
   - Lead with strongest benefit or unique feature
   - Include brand/character name
   - Add emotional hook
   - Example: "Authentic Minion figurine from Despicable Me - features detailed prison outfit, vibrant colors, and durable construction. Perfect for collectors and fans!"

7. PRIMARY KEYWORDS (CRITICAL - MUST PROVIDE 8-12 KEYWORDS):
   REQUIREMENT: Generate exactly 8-12 primary keywords (not fewer, not more)

   Include in priority order:
   1. Brand/Character name (if recognizable)
   2. Franchise name (if applicable)
   3. Product type (specific, not generic)
   4. Material
   5. Color
   6. Primary feature
   7. Use case
   8. Target audience
   9-12. Related search terms

   For licensed/branded products, ALWAYS include franchise name
   Example for Minion: ["Minion", "Despicable Me", "figurine", "collectible", "toy", "character", "plastic", "yellow", "gift", "desk decor", "fan merchandise", "movie character"]

   AVOID: Stop words ("the", "a", "an"), overly generic terms ("thing", "item", "product")

8. LONG-TAIL KEYWORDS (5-8 phrases, 3-5 words each):
   Format: [Brand/Character] + [Product Type] + [Qualifier]
   Include: Search intent phrases, gift phrases, comparison phrases
   Example: "Minion collectible figurine toy", "Despicable Me character gift", "yellow Minion desk decoration", "authentic Minion figure for fans"

9. FEATURE HIGHLIGHTS (CRITICAL - MUST PROVIDE 5-7 BULLET POINTS):
   REQUIREMENT: Generate exactly 5-7 feature bullet points (not fewer, not more)

   Each bullet must:
   - Start with a BENEFIT, not just a feature
   - Be specific and concrete (not generic)
   - Use benefit-driven language
   - Be concise (one clear sentence)

   Include mix of:
   - Brand authentication (if applicable)
   - Key visual features with benefits
   - Quality indicators with value
   - Use cases with user outcomes
   - Emotional benefits

   Examples of GOOD bullets:
   ✓ "Authentic Minion character design from Despicable Me brings beloved movie character to life"
   ✓ "Vibrant yellow color with detailed outfit captures iconic look perfectly"
   ✓ "Durable plastic construction ensures long-lasting display and play"

   Examples of BAD bullets:
   ✗ "Yellow" (too generic, no benefit)
   ✗ "It has features" (meaningless)
   ✗ "Made of material" (vague, uninformative)

10. SKU INTELLIGENCE:
    - For branded products, include brand abbreviation: "DM-MIN-YEL-001" (Despicable Me)
    - Format: [BRAND]-[CATEGORY]-[COLOR]-[VARIANT]
    - Variant signals: Include any visible variations (colors, sizes, character variants)
    - Bundle pairings: Suggest complementary items from same franchise or category"""

    if image_count > 1:
        multi_image_rules = """

MULTI-IMAGE ANALYSIS:
You have been provided with multiple images of the same product. Use all images to:
1. Synthesize a complete understanding - different angles reveal different attributes
2. Prioritize front/hero shots for primary features
3. Use detail shots for material, finish, and construction insights
4. Use lifestyle/context shots for target demographic and occasion
5. If images show variations (colors, sizes), note them in variant_signals
6. Higher confidence scores when multiple angles confirm the same attribute"""
        base_prompt += multi_image_rules

    base_prompt += """

Remember: Output ONLY valid JSON, nothing else."""

    return base_prompt


def build_chat_prompt(history: List[ChatMessage], product_data: dict = None) -> str:
    """Build the prompt for chat interactions with product context."""

    system_prompt = """You are a visual product analysis specialist helping users understand product details from retail images.

ROLE: Answer questions about the product shown in the image(s) using both visual evidence and previously extracted product data.

RULES:
1. Use the PRODUCT ANALYSIS DATA below as your primary knowledge base for this product
2. For content generation requests (descriptions, titles, marketing copy), use the existing data as a foundation
3. Provide helpful, direct answers without unnecessary disclaimers or preambles
4. Use professional retail and merchandising vocabulary
5. If asked for SEO content, formats, or descriptions, provide well-structured, detailed responses
6. Be creative and helpful when asked to generate marketing content
7. Answer questions naturally and conversationally - focus on being helpful

"""

    # Add product analysis data if available
    if product_data:
        system_prompt += """PRODUCT ANALYSIS DATA (Use this information to answer questions):

"""
        if "content_package" in product_data:
            cp = product_data["content_package"]

            # Product Identity
            if "product_identity" in cp:
                pi = cp["product_identity"]
                system_prompt += f"Category: {pi.get('category', 'N/A')}\n"
                system_prompt += f"Subcategory: {pi.get('subcategory', 'N/A')}\n"
                system_prompt += f"Price Positioning: {pi.get('price_positioning', 'N/A')}\n"
                system_prompt += f"Marketing Tagline: {pi.get('marketing_tagline', 'N/A')}\n\n"

            # Titles & Descriptions
            if "titles_descriptions" in cp:
                td = cp["titles_descriptions"]
                system_prompt += f"SEO Title: {td.get('seo_title', 'N/A')}\n"
                system_prompt += f"Short Description: {td.get('short_description', 'N/A')}\n"
                system_prompt += f"Long Description: {td.get('long_description', 'N/A')}\n\n"

            # Attributes
            if "attributes" in cp:
                system_prompt += "Attributes:\n"
                for attr_name, attr_data in cp["attributes"].items():
                    value = attr_data.get('value', 'N/A')
                    conf = attr_data.get('confidence', 0)
                    system_prompt += f"  - {attr_name}: {value} (confidence: {conf:.0%})\n"
                system_prompt += "\n"

            # Feature Highlights
            if "feature_highlights" in cp:
                system_prompt += "Feature Highlights:\n"
                for feature in cp["feature_highlights"]:
                    system_prompt += f"  - {feature}\n"
                system_prompt += "\n"

            # SEO Keywords
            if "seo_keywords" in cp:
                kw = cp["seo_keywords"]
                if "primary" in kw:
                    system_prompt += f"Primary Keywords: {', '.join(kw['primary'])}\n"
                if "long_tail" in kw:
                    system_prompt += f"Long-tail Keywords: {', '.join(kw['long_tail'])}\n"
                system_prompt += "\n"

            # SKU Intelligence
            if "sku_intelligence" in cp:
                sku = cp["sku_intelligence"]
                system_prompt += "SKU Intelligence:\n"
                system_prompt += f"  Suggested SKU: {sku.get('naming_suggestion', 'N/A')}\n"
                if "variant_signals" in sku and sku["variant_signals"]:
                    system_prompt += f"  Variant Signals: {', '.join(sku['variant_signals'])}\n"
                if "bundle_pairings" in sku and sku["bundle_pairings"]:
                    system_prompt += f"  Bundle Pairings: {', '.join(sku['bundle_pairings'])}\n"
                system_prompt += "\n"

    system_prompt += """CONVERSATION HISTORY:"""

    # Add conversation history
    for msg in history:
        role_label = "User" if msg.role == "user" else "Assistant"
        system_prompt += f"\n{role_label}: {msg.content}"

    return system_prompt


def generate_suggested_questions(category: str, attributes: dict) -> List[str]:
    """Generate contextual suggested questions based on product analysis."""

    questions = [
        "What material is this product made from?",
        "Who is the target customer for this product?",
        "What are the key features I should highlight?",
    ]

    # Add category-specific questions
    category_lower = category.lower()

    if "fashion" in category_lower or "apparel" in category_lower or "clothing" in category_lower:
        questions.append("What occasions is this suitable for?")
        questions.append("What style category does this fall into?")
    elif "home" in category_lower or "furniture" in category_lower:
        questions.append("What room or space is this designed for?")
        questions.append("What design style does this represent?")
    elif "electronics" in category_lower or "tech" in category_lower:
        questions.append("What are the main use cases for this product?")
        questions.append("What type of user would benefit most from this?")
    else:
        questions.append("What makes this product unique?")
        questions.append("How should this be positioned in the market?")

    return questions[:5]  # Return max 5 questions
