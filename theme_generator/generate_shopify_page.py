import os
import json
import asyncio
import base64
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from PIL import Image
import glob
import argparse
import re
import aiohttp
load_dotenv()

# Initialize Claude LLM
shopify_llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature=0.1,
    max_tokens=40000  # Increased for complex page generation
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

class ShopifyPageGenerator:
    def __init__(self, sections_dir, shopify_code_dir, output_dir):
        """Initialize the generator with sections, shopify code, and output directories."""
        self.sections_dir = sections_dir
        self.shopify_code_dir = shopify_code_dir
        self.output_dir = output_dir

    def _find_section_files(self) -> list:
        """Find all section files in order (01-, 02-, etc.)."""
        if not os.path.exists(self.sections_dir):
            raise FileNotFoundError(f"Sections directory not found: {self.sections_dir}")
        pattern = "[0-9][0-9]-*.md"
        matching_files = glob.glob(os.path.join(self.sections_dir, pattern))
        if not matching_files:
            raise FileNotFoundError(f"No section files found in {self.sections_dir}")
        matching_files.sort(key=lambda x: int(os.path.basename(x).split('-')[0]))
        return [os.path.basename(f) for f in matching_files]

    def _get_section_schema(self, section_file: str) -> str:
        """Extract schema from generated section liquid file."""
        section_name = section_file.replace('.md', '.liquid')
        section_path = os.path.join(self.shopify_code_dir, section_name)
        if not os.path.exists(section_path):
            raise FileNotFoundError(f"Section file not found: {section_path}")
        try:
            with open(section_path, 'r', encoding='utf-8') as f:
                content = f.read()
            schema_match = re.search(r'{%\s*schema\s*%}(.*?){%\s*endschema\s*%}', content, re.DOTALL)
            if not schema_match:
                raise ValueError(f"No schema found in {section_name}")
            return schema_match.group(1).strip()
        except Exception as e:
            print(f"Warning: Could not read schema from {section_path}: {e}")
            return ""

    def _get_section_content(self, section_file: str) -> str:
        """Get section markdown content."""
        section_path = os.path.join(self.sections_dir, section_file)
        if not os.path.exists(section_path):
            raise FileNotFoundError(f"Section file not found: {section_path}")
        try:
            with open(section_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not read {section_path}: {e}")
            return ""

    async def generate_page_code(self, output_file: str = None):
        try:
            section_files = self._find_section_files()
            if not section_files:
                raise ValueError("No section files found")
            os.makedirs(self.output_dir, exist_ok=True)
            # Prepare the prompts
            system_prompt = f"""
            You are a Shopify Template architect specialized in creating cohesive page layouts.
            Create a complete page implementation that combines multiple sections in a specific order.

            Your task is to:
            1. Create a detailed implementation plan
            2. Generate the page.custom.json template that includes all sections
            3. Ensure proper section ordering and integration

            Required File Structure:
            - templates/page.custom.json (main page template with all sections)

            Focus on:
            - Proper section ordering
            - Section integration and spacing
            - Responsive layout
            - Performance optimization
            - Proper schema usage

            Technical Requirements:
            - Must work with Shopify 2.0 architecture
            - Use json templates for page structure
            - Include all section schemas
            - Maintain section order
            - Implement responsive design
            - Include proper error handling

            CRITICAL INSTRUCTION: The page template must include all sections in the exact order provided,
            with their schemas properly integrated.

            CRITICAL INSTRUCTION FOR CODE BLOCKS OUTPUT FORMAT: When showing implementation code, follow this exact format:
            ---
            FILE: templates/page.custom.json
            TYPE: json
            CONTENT:
            ```json
            [actual code content]
            ```
            ---
            """
            sections_info = []
            for section_file in section_files:
                section_content = self._get_section_content(section_file)
                section_schema = self._get_section_schema(section_file)
                sections_info.append({
                    "file": section_file,
                    "content": section_content,
                    "schema": section_schema
                })
            user_prompt = f"""
            Generate a complete Shopify page implementation that combines the following sections in order:

            Current Date and Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            Store Data that can be used for the offer page:
            - Collection Handle: all 

            Sections to include (in order):
            {json.dumps([{"filename": "sections/" + s["file"], "content": s["content"], "schema": s["schema"]} for s in sections_info], indent=2)}

            Please generate a complete, production-ready Shopify page implementation that:
            1. Includes all sections in the specified order
            2. Properly integrates section schemas
            3. Is responsive and accessible
            4. Follows Shopify best practices
            5. Has proper error handling
            6. Is optimized for performance
            7. settings of each section are according to the section design in the content
            8. keep the type of the section same as the filename

            Generate the code in the specified format, ensuring it follows Shopify's requirements and best practices.
            """
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = await shopify_llm.ainvoke(messages)
            response_file = os.path.join(self.output_dir, "generated_page_code.txt")
            with open(response_file, "w", encoding="utf-8") as f:
                f.write(response.content)
            file_pattern = r"---\s*FILE:\s*([^\n]+)\s*TYPE:\s*([^\n]+)\s*CONTENT:\s*```(?:[^\n]*)\n([\s\S]*?)```\s*---"
            for match in re.finditer(file_pattern, response.content):
                file_path = match.group(1).strip()
                file_type = match.group(2).strip()
                file_content = match.group(3).strip()
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(file_content)
            print(f"\n✅ Shopify page code generated and saved to: {self.output_dir}")
            print("\nGenerated files:")
            for root, _, files in os.walk(self.output_dir):
                for file in files:
                    if not file.endswith("_code.txt"):
                        print(f"- {os.path.relpath(os.path.join(root, file), self.output_dir)}")
            return response.content
        except Exception as e:
            print(f"Error generating Shopify page code: {str(e)}")
            return None

async def main():
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ Missing ANTHROPIC_API_KEY environment variable")
    parser = argparse.ArgumentParser(description="Generate Shopify page code from design documentation")
    parser.add_argument("--sections-dir", required=True, help="Directory containing parsed section markdown files")
    parser.add_argument("--shopify-code-dir", required=True, help="Directory containing generated section .liquid files")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated page code and templates")
    parser.add_argument("--output-file", help="Output file path for the main page JSON (e.g., index.json)")
    args = parser.parse_args()
    generator = ShopifyPageGenerator(sections_dir=args.sections_dir, shopify_code_dir=args.shopify_code_dir, output_dir=args.output_dir)
    try:
        await generator.generate_page_code(output_file=args.output_file)
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 