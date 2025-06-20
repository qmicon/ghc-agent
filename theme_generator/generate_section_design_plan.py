#!/usr/bin/env python3
"""
generate_section_design_plan.py
-----------------------------------------------------------------
Generates detailed markdown-based design plans for each section of a website,
based on design documentation and screenshots. The output is structured for
frontend developers to understand and implement the design.
"""

import os
import asyncio
import base64
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from PIL import Image
import glob
import argparse

load_dotenv()

# Initialize Claude LLM
design_llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature=0.1,
    max_tokens=40000  # Increased for detailed section analysis
).with_retry(
    stop_after_attempt=5,  # Maximum number of attempts
    wait_exponential_jitter=True,  # Add jitter to the exponential backoff
    retry_if_exception_type=(Exception,),  # Retry on any exception
    exponential_jitter_params={
        "initial": 5,  # Initial delay in seconds
        "max": 60,  # Maximum delay in seconds
        "exp_base": 2,  # Base for exponential backoff
        "jitter": 0.1  # Random jitter factor
    }
)

class SectionDesignAnalyzer:
    def __init__(self, design_docs_dir, screenshots_dir, output_dir):
        """Initialize the analyzer with design docs, screenshots, and output directories."""
        self.design_docs_dir = design_docs_dir
        self.screenshots_dir = screenshots_dir
        self.output_dir = output_dir

    def _get_design_docs(self):
        """Get all design documentation in the design docs directory."""
        design_docs = []
        md_files = glob.glob(os.path.join(self.design_docs_dir, "*_design.md"))
        for md_file in sorted(md_files):
            with open(md_file, "r", encoding="utf-8") as f:
                design_docs.append({
                    "filename": os.path.basename(md_file),
                    "content": f.read()
                })
        return design_docs

    def _get_screenshots(self):
        """Get all screenshots in the screenshots directory."""
        screenshots = []
        png_files = glob.glob(os.path.join(self.screenshots_dir, "???-shopify-section-*.png"))
        for png_file in sorted(png_files):
            with open(png_file, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                screenshots.append({
                    "filename": os.path.basename(png_file),
                    "data": image_data
                })
        return screenshots

    def _parse_and_save_sections(self, content: str, output_dir: str):
        """Parse markdown content and save individual section files."""
        import re
        
        # First find all headings to identify section boundaries
        heading_pattern = r"^(#{1,8})\s+([^\n]+)$"
        all_headings = list(re.finditer(heading_pattern, content, re.MULTILINE))
        
        # Filter only level 1 headings
        level1_headings = [
            (heading.start(), heading.end(), heading.group(2).strip())
            for heading in all_headings
            if len(heading.group(1)) == 1
        ]
        
        if not level1_headings:
            print("Warning: No level 1 headings found in the content")
            return []
        
        # Create sections directory
        sections_dir = os.path.join(output_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)
        
        saved_files = []
        for i, (start_pos, end_pos, section_name) in enumerate(level1_headings, 1):  # Start enumeration from 1
            # Get content until next level 1 heading or end of file
            next_start = level1_headings[i][0] if i < len(level1_headings) else len(content)
            section_content = content[end_pos:next_start].strip()
            
            # Create a safe filename from the section name
            safe_filename = re.sub(r'[^\w\s-]', '', section_name.lower())
            safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
            # Add numerical prefix with padding (e.g., 01-, 02-, etc.)
            section_file = os.path.join(sections_dir, f"{i:02d}-{safe_filename}.md")
            
            # Write section content to file
            with open(section_file, "w", encoding="utf-8") as f:
                f.write(f"# {section_name}\n\n{section_content}")
            saved_files.append(section_file)
        
        return saved_files

    async def generate_section_plans(self):
        """Generate detailed design plans for each section."""
        design_docs = self._get_design_docs()
        screenshots = self._get_screenshots()
        if not design_docs or not screenshots:
            raise ValueError("No design docs or screenshots found")
        # Prepare the prompts
        system_prompt = """
        You are a senior frontend developer and UI/UX expert tasked with creating detailed design plans for website sections.
        
        Your task is to analyze the design documentation and screenshots to create comprehensive markdown-based design plans
        for each section of the website. These plans will be used by frontend developers to implement the design accurately.

        For each section, provide a detailed analysis in markdown format with the following structure:

        # [Section Name]
        
        ## Overview
        - Brief description of the section's purpose and role in the page
        - Key user interactions and goals
        - Content hierarchy and importance
        
        ## Visual Design
        ### Layout
        - Grid system and responsive breakpoints
        - Spacing and alignment specifications
        - Container widths and padding
        - Component positioning and relationships
        
        ### Typography
        - Font families and weights
        - Font sizes for different elements
        - Line heights and letter spacing
        - Text colors and contrast ratios
        - Text alignment and wrapping rules
        
        ### Colors
        - Primary and secondary color palette
        - Background colors and gradients
        - Text colors and contrast
        - Accent colors and highlights
        - Hover and active states
        
        ### Images and Media
        - Image specifications (dimensions, formats)
        - Image placement and scaling rules
        - Media queries for responsive images
        - Alt text requirements
        - Loading and optimization guidelines
        
        ## Interactive Elements
        ### Buttons and Links
        - Button styles and variations
        - Hover and active states
        - Focus states and accessibility
        - Link styles and behaviors
        - Icon usage and placement
        
        ### Forms and Inputs
        - Input field styles
        - Validation states and feedback
        - Error handling and messages
        - Form layout and spacing
        - Submit button behavior
        
        ### Animations and Transitions
        - Hover effects
        - Loading states
        - Transition timings
        - Animation triggers
        - Performance considerations
        
        ## Responsive Behavior
        - Breakpoint specifications
        - Layout changes at each breakpoint
        - Content reordering rules
        - Image and media handling
        - Touch interaction considerations
        
        ## Accessibility
        - ARIA roles and labels
        - Keyboard navigation
        - Focus management
        - Color contrast requirements
        - Screen reader considerations
        
        ## Technical Implementation Notes
        - CSS architecture recommendations
        - Component structure
        - State management approach
        - Performance optimization tips
        - Browser compatibility notes
        
        ## Code Examples
        ```html
        <!-- Example HTML structure -->
        ```
        
        ```css
        /* Example CSS styles */
        ```
        
        ```javascript
        // Example JavaScript behavior
        ```
        
        Focus on providing clear, actionable guidance that frontend developers can use to implement the design accurately.
        Include specific measurements, colors, and other design tokens where possible.
        """

        # Prepare design docs and screenshots for the prompt
        docs_text = "\n\n".join([f"## {doc['filename']}\n{doc['content']}" for doc in design_docs])
        
        user_prompt = f"""
        Create detailed design plans for each section of the website based on the following design documentation and screenshots.

        Design Documentation:
        {docs_text}

        Screenshots:
        {len(screenshots)} screenshots provided for reference.

        Please analyze the design documentation and screenshots to create comprehensive design plans for each section.
        Focus on providing clear, actionable guidance for frontend developers.
        Include specific measurements, colors, and other design tokens where possible.
        """

        # Create messages for Claude
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=[
                {"type": "text", "text": user_prompt},
                *[{
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot["data"]
                    }
                } for screenshot in screenshots]
            ])
        ]

        try:
            # Get design plans from Claude
            response = await design_llm.ainvoke(messages)
            content = response.content.strip()
            
            # Save the design plans
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Save raw response
            raw_file = os.path.join(self.output_dir, "raw_section_plans.txt")
            with open(raw_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"\n✓ Raw section plans saved to {raw_file}")
            
            # Save formatted markdown
            plans_file = os.path.join(self.output_dir, "section_design_plans.md")
            with open(plans_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ Section design plans saved to {plans_file}")
            
            # Parse and save individual section files
            section_files = self._parse_and_save_sections(content, self.output_dir)
            print("\n✓ Individual section files saved:")
            for section_file in section_files:
                print(f"  - {os.path.relpath(section_file, self.output_dir)}")
            
            return content
            
        except Exception as e:
            print(f"Error generating section design plans: {str(e)}")
            return None

    def parse_existing_plans(self):
        """Parse an existing section_design_plans.md file into individual section files."""
        plans_file = os.path.join(self.output_dir, "section_design_plans.md")
        if not os.path.exists(plans_file):
            raise FileNotFoundError(f"Section design plans not found at {plans_file}")
        
        try:
            with open(plans_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            section_files = self._parse_and_save_sections(content, self.output_dir)
            print("\n✓ Individual section files saved:")
            for section_file in section_files:
                print(f"  - {os.path.relpath(section_file, self.output_dir)}")
            
            return section_files
            
        except Exception as e:
            print(f"Error parsing section design plans: {str(e)}")
            return None

async def main():
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")
    parser = argparse.ArgumentParser(description="Generate or parse detailed design plans for website sections")
    parser.add_argument("--design-docs-dir", required=True, help="Directory containing design docs (*.md)")
    parser.add_argument("--screenshots-dir", required=True, help="Directory containing screenshots (*.png)")
    parser.add_argument("--output-dir", required=True, help="Directory to save section design plans and parsed sections")
    parser.add_argument("--parse-only", action="store_true", help="Only parse existing section_design_plans.md into individual section files")
    args = parser.parse_args()
    analyzer = SectionDesignAnalyzer(design_docs_dir=args.design_docs_dir, screenshots_dir=args.screenshots_dir, output_dir=args.output_dir)
    if args.parse_only:
        print(f"\nParsing existing section design plans...")
        analyzer.parse_existing_plans()
    else:
        print(f"\nGenerating section design plans...")
        await analyzer.generate_section_plans()

if __name__ == "__main__":
    asyncio.run(main()) 