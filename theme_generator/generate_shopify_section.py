#!/usr/bin/env python3
"""
generate_shopify_section.py
-----------------------------------------------------------------
Generates a Shopify section.liquid file from a section design markdown file.
Uses the same pattern and prompts as generate_shopify_page.py but focuses on
a single section implementation.
"""

import os
import asyncio
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import argparse
import glob

load_dotenv()

# Initialize Claude LLM
shopify_llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature=0.1,
    max_tokens=40000  # Increased for complex section generation
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

def load_examples(examples_dir: str, section_number: int) -> str:
    """Load examples from examples.txt file in the examples directory."""
    try:
        examples_file = os.path.join(examples_dir, f"{section_number:02d}-examples.txt")
        with open(examples_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: examples.txt not found at {examples_file}")
        return ""
    except Exception as e:
        print(f"Warning: Error reading examples.txt: {e}")
        return ""

def get_all_section_files(sections_dir: str) -> list:
    """Get all section files from the sections directory."""
    if not os.path.exists(sections_dir):
        raise FileNotFoundError(f"Sections directory not found: {sections_dir}")
    section_files = []
    for file in glob.glob(os.path.join(sections_dir, "*.md")):
        try:
            section_number = int(os.path.basename(file).split("-")[0])
            section_files.append((section_number, os.path.basename(file)))
        except (ValueError, IndexError) as e:
            print(f"Warning: Invalid section filename format: {file}")
    section_files.sort(key=lambda x: x[0])
    return section_files

class ShopifySectionGenerator:
    def __init__(self, sections_dir, examples_dir, output_dir):
        """Initialize the generator with sections, examples, and output directories."""
        self.sections_dir = sections_dir
        self.examples_dir = examples_dir
        self.output_dir = output_dir

    def _find_section_file(self, section_number: int) -> str:
        """Find the section file that starts with the given number."""
        if section_number < 1:
            raise ValueError("Section number must be positive")
        pattern = f"{section_number:02d}-*.md"
        matching_files = glob.glob(os.path.join(self.sections_dir, pattern))
        if not matching_files:
            raise FileNotFoundError(f"No section file found starting with {section_number}- in {self.sections_dir}")
        if len(matching_files) > 1:
            raise ValueError(f"Multiple section files found starting with {section_number}- in {self.sections_dir}")
        return os.path.basename(matching_files[0])

    def _get_section_design(self, section_number: int):
        """Get the section design markdown content."""
        section_file = self._find_section_file(section_number)
        design_file = os.path.join(self.sections_dir, section_file)
        with open(design_file, "r", encoding="utf-8") as f:
            return f.read(), section_file

    async def generate_section_code(self, section_number: int):
        section_design, section_file = self._get_section_design(section_number)
        examples = load_examples(self.examples_dir, section_number)

        system_prompt = f"""
        You are a Shopify Liquid architect specialized in designing high-impact sections.
        Create a complete section implementation from scratch based on the provided section design documentation.

        Your task is to create a detailed implementation plan that includes:
        1. Step-by-step implementation guide
        2. Detailed implementation instructions
        3. Actual code blocks that follows the implementation instructions

        Required File Structure:
        - sections/{section_file.replace('.md', '.liquid')} (main section file with all the code)

        Focus on:
        - Clear component structure
        - Modern, responsive design
        - User-friendly interface
        - Step-by-step implementation details
        - File structure and organization
        - Proper error handling and validation

        Technical Requirements:
        - Must work with Shopify 2.0 architecture
        - Use liquid templates for section structure
        - Create all components from scratch
        - Implement modern, responsive design
        - Include proper error handling and validation

        Required File Structure:
        1. sections/{section_file.replace('.md', '.liquid')}
           - Must define section schema
           - Must be valid liquid format
           - Include all necessary CSS and JavaScript
           - Use proper snippet includes

        Please provide a detailed written plan that includes:

        1. Implementation Steps
        - Step-by-step guide on how to implement the section
        - Order of implementation
        - Dependencies between components

        2. Required Components
        - List of all snippets needed
        - Purpose and functionality of each component
        - How components will interact with each other

        3. Implementation Notes
        - Detailed description of implementation notes
        - Explain the logic and reasoning behind the implementation code
        - Explain architecture decisions and trade-offs
        - Document error handling strategy

        After the plan is generated, generate the code while following these instructions:

        1. The code follows modern web development best practices and patterns
        2. Components are well-structured and maintainable
        3. User interactions are handled efficiently and reliably
        4. Error cases are handled gracefully
        5. Avoid using local storage as states get corrupted when the page is loaded in a new tab

        CRITICAL INSTRUCTION: A plan should contain all the detailed information so that a beginner Shopify developer could save the implementation to files and it would work without any additional guidance.

        CRITICAL INSTRUCTION FOR CODE BLOCKS OUTPUT FORMAT: When showing implementation code, follow this exact format:
        ---
        FILE: {section_file.replace('.md', '.liquid')}
        TYPE: liquid
        CONTENT:
        ```liquid
        [actual code content]
        ```
        ---

        CRITICAL VALIDATION INSTRUCTIONS:
        1. Picker settings of types article, blog, collection, collection_list, product, and product_list
        MUST NOT include any `default` attribute in section schemas.
        2. Liquid templates under sections/ must have all code according to the requirements.
        3. Do not use filters (e.g., | times) directly within tag parameters like limit in for loops or conditions in if statements. Instead, perform calculations separately using the assign tag with unique variable names, then reference the resulting variable within your tags.
        4. Do not use limit as a filter within assign statements. The limit keyword is a parameter for for loops, not a filter. To limit the number of items in an array outside of a loop, use the slice filter
        5. Do not include limit parameters within if statements. The limit parameter is not valid in this context and will cause syntax errors.
        6. When you need to retrieve the first item from a filtered collection, use the first filter instead of combining where with limit.
        7. Range settings in the section schema must have at least 3 steps, which means the difference between the min and max value should be at least 3 times the step value.
        8. Avoid embedding Liquid output tags ({{ }}) directly within JavaScript template literals. Instead, assign the desired Liquid output to a variable using the assign tag and reference that variable within your JavaScript code.
        9. Avoid using Liquid filters or expressions directly within tag parameters. Instead, assign the result to a variable before using it in the tag.

        Below are some examples of how the code developed by shopify developers looks like:
        {examples}

        Use these examples as reference for:
        - File structure and organization
        - Component architecture and patterns
        - Implementation approaches
        - Best practices for Shopify theme development

        Do not copy the examples directly - instead, understand the patterns and adapt them to the mentioned requirements.
        """

        user_prompt = f"""
        Generate a complete Shopify section implementation based on the following section design documentation.

        Section File: {section_file}

        Section Design Documentation:
        {section_design}

        Current Date and Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        Please generate a complete, production-ready Shopify section implementation that:
        1. Matches the design documentation
        2. Is responsive and accessible
        3. Follows Shopify best practices
        4. Includes all necessary components
        5. Has proper error handling
        6. Is optimized for performance

        Generate the code in the specified format, ensuring it follows Shopify's requirements and best practices.
        """

        # Create messages for Claude
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            # Get code generation from Claude
            response = await shopify_llm.ainvoke(messages)
            os.makedirs(self.output_dir, exist_ok=True)
            output_file = os.path.join(self.output_dir, f"generated_{section_file.replace('.md', '_code.txt')}")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.content)
            # Extract and save individual files
            import re
            file_pattern = r"---\s*FILE:\s*([^\n]+)\s*TYPE:\s*([^\n]+)\s*CONTENT:\s*```(?:[^\n]*)\n([\s\S]*?)```\s*---"
            for match in re.finditer(file_pattern, response.content):
                file_path = match.group(1).strip()
                file_type = match.group(2).strip()
                file_content = match.group(3).strip()
                full_path = os.path.join(self.output_dir, file_path.lstrip("/"))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
            print(f"\n✅ Shopify section code generated and saved to: {self.output_dir}")
            print("\nGenerated files:")
            for root, _, files in os.walk(self.output_dir):
                for file in files:
                    if not file.endswith("_code.txt"):
                        print(f"- {os.path.relpath(os.path.join(root, file), self.output_dir)}")
            return response.content
        except Exception as e:
            print(f"Error generating Shopify section code: {str(e)}")
            return None

    async def generate_all_sections(self):
        try:
            section_files = get_all_section_files(self.sections_dir)
            if not section_files:
                raise ValueError("No section files found")
            print(f"\nFound {len(section_files)} sections to process")
            for section_num, section_file in section_files:
                print(f"\nProcessing section {section_num}: {section_file}")
                try:
                    await self.generate_section_code(section_num)
                except Exception as e:
                    print(f"Warning: Failed to process section {section_num}: {str(e)}")
                    continue
            print("\n✅ All sections processed successfully!")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

async def main():
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ Missing ANTHROPIC_API_KEY environment variable")
    parser = argparse.ArgumentParser(description="Generate Shopify section code from section design documentation")
    parser.add_argument("--sections-dir", required=True, help="Directory containing parsed section markdown files")
    parser.add_argument("--examples-dir", required=True, help="Directory containing examples for each section")
    parser.add_argument("--section", type=int, help="Optional: Section number to generate code for (e.g., 1 for 01-hero-section.md). If not provided, processes all sections.")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated Shopify section code")
    args = parser.parse_args()
    generator = ShopifySectionGenerator(sections_dir=args.sections_dir, examples_dir=args.examples_dir, output_dir=args.output_dir)
    try:
        if args.section is not None:
            await generator.generate_section_code(args.section)
        else:
            print("\nNo section number provided. Processing all sections...")
            await generator.generate_all_sections()
    except ValueError as e:
        print(f"❌ Validation Error: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 