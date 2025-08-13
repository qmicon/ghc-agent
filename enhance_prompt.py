import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
load_dotenv()

template = """
# Shopify Page Prompt Enhancement Instruction Template

## Overview

Create structured, detailed prompts for Shopify page development that include comprehensive specifications for layout, functionality, and design elements. The prompts should follow a hierarchical structure with clearly defined sections covering general settings, major page components, and detailed feature requirements.

## Prompt Structure

1. **Title and Purpose**: Begin with a clear title identifying the page type (Product Page, Collection Page, etc.) and a one-sentence description of the purpose.

2. **General Settings**: Include technical requirements and foundation settings:
   - Product/collection data retrieval method (API endpoints, handles)
   - SEO requirements (meta tags, structured data)
   - Compatibility specifications (Online Store 2.0, sections)
   - Schema.org structured data requirements (JSON-LD format)

3. **Major Sections**: Organize the page into logical components with numbered sections:
   - Hero/Media section
   - Product/Content information section
   - Additional feature sections (subscribe & save, testimonials, recommendations)
   - Footer/supplementary sections

4. **Component Details**: For each section, include these elements when applicable:
   - Visual layout specifications (grid, columns, positioning)
   - Content elements (titles, descriptions, prices, images)
   - Dynamic data usage (product.title, metafields, inventory quantity)
   - Design specifications (colors with hex codes, typography, spacing)
   - Responsive behavior requirements

5. **Interactive Elements**:
   - Form functionality (product forms, add to cart)
   - Call-to-action buttons (styling, text, placement)
   - User interaction patterns (hover effects, transitions)
   - Loading states and animations

6. **Visual Design Specifications**:
   - Color schemes with specific hex codes
   - Typography hierarchy (font weights, sizes)
   - UI components (cards, badges, icons)
   - Spacing and layout parameters

7. **Functional Requirements**:
   - Technical implementation details
   - Liquid template requirements
   - JavaScript functionality
   - Responsive design specifications
   - Performance considerations
   - avoid code examples so that technical product manager can understand the prompt better

## Formatting Guidelines

1. **Numbered Instructions**: Use sequential numbering for all major requirements.

2. **Visual Hierarchy**: Use appropriate spacing and formatting to distinguish between:
   - Major sections (with clear headings)
   - Subsections (with indentation or prefixes)
   - Specific elements (as bulleted or check-marked lists)

3. **Technical Specifications**: 
   - Include specific Liquid syntax in code format: `{{ product.title }}`
   - Provide exact CSS property values: `(#FF7F7F)`
   - Specify conditional logic where needed

4. **Design Elements**:
   - Use descriptive section names with emoji indicators where appropriate
   - Include visual cues for design elements (✅, 🧩, etc.)
   - Provide clear styling instructions (borders, shadows, colors)

5. **Data Requirements**:
   - Specify exactly which product data to use
   - Include instructions for handling missing data
   - Provide fallback options where appropriate

## Content Specificity

1. **Product Information**: Specify exactly which product fields to display:
   - Title formatting
   - Price display (with sale price logic)
   - Description formatting (truncation requirements)
   - Image gallery specifications

2. **Trust Elements**:
   - Include specific trust indicators (reviews, approvals, badges)
   - Provide statistical claims with exact percentages
   - Format testimonial and social proof elements

3. **Conversion Elements**:
   - Subscription offers with specific discount percentages
   - Timeline-based benefits with statistical support
   - Call-to-action button styling and text

4. **Related Products**:
   - Specifications for product recommendation algorithms
   - Card design and layout for related products
   - Badge and offer strip requirements

## Example Templates

Include modular sections that can be combined for different page types:

1. **Hero Image Gallery Template**
2. **Product Information Display Template**
3. **Subscription Offer Template**
4. **Benefits Timeline Display Template**
5. **Testimonial Display Template**
6. **Related Products Template**

Use these templates to create comprehensive page prompts that produce consistent, high-quality Shopify pages with all necessary functionality and design elements.
"""

def enhance_prompt(input_path="simple_offer_requirement.txt", output_path="enhanced_prompt.txt"):
    # Read the simple prompt
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            simple_prompt = f.read()
    except FileNotFoundError:
        print(f"❌ {input_path} not found")
        return

    # Prepare the enhancement instruction
    instruction = (
        "You are an expert Shopify theme developer and product manager. "
        "Given the following simple offer requirement, rewrite and expand it into a detailed, actionable, and unambiguous implementation prompt. "
        "Follow the complete Shopify Page Prompt Enhancement Instruction Template below to structure your response:\n\n"
        f"{template}\n\n"
        "Simple requirement:\n"
        "------------------\n"
        f"{simple_prompt}\n"
        "------------------\n"
        "Enhanced prompt:"
    )

    # Initialize Claude
    llm = ChatAnthropic(
        model="claude-3-7-sonnet-latest",
        temperature=0.1,
        max_tokens=6000
    )

    # Get the enhanced prompt
    resp = llm.invoke([HumanMessage(content=instruction)])
    enhanced = resp.content.strip()

    # Save to output file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(enhanced)
    print(f"✓ Enhanced prompt saved to {output_path}")

if __name__ == "__main__":
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")
    enhance_prompt()