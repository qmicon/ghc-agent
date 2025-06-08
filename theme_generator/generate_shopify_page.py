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
    def __init__(self, screenshots_dir="screenshots"):
        """Initialize the generator with screenshots directory."""
        self.screenshots_dir = screenshots_dir

    def _find_section_files(self, website: str, viewport: str) -> list:
        """Find all section files in order (01-, 02-, etc.)."""
        sections_dir = os.path.join("screenshots", website, viewport, "design_docs", "sections")
        if not os.path.exists(sections_dir):
            raise FileNotFoundError(f"Sections directory not found: {sections_dir}")
        
        # Look for all numbered section files
        pattern = "[0-9][0-9]-*.md"
        matching_files = glob.glob(os.path.join(sections_dir, pattern))
        
        if not matching_files:
            raise FileNotFoundError(f"No section files found in {sections_dir}")
        
        # Sort files by their number prefix
        matching_files.sort(key=lambda x: int(os.path.basename(x).split('-')[0]))
        return [os.path.basename(f) for f in matching_files]

    def _get_section_schema(self, section_file: str, shopify_code_dir: str) -> str:
        """Extract schema from generated section liquid file."""
        section_name = section_file.replace('.md', '.liquid')
        section_path = os.path.join(shopify_code_dir, section_name)
        
        if not os.path.exists(section_path):
            raise FileNotFoundError(f"Section file not found: {section_path}")
        
        try:
            with open(section_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract schema block
            schema_match = re.search(r'{%\s*schema\s*%}(.*?){%\s*endschema\s*%}', content, re.DOTALL)
            if not schema_match:
                raise ValueError(f"No schema found in {section_name}")
                
            return schema_match.group(1).strip()
        except Exception as e:
            print(f"Warning: Could not read schema from {section_path}: {e}")
            return ""

    def _get_section_content(self, section_file: str, website: str, viewport: str) -> str:
        """Get section markdown content."""
        section_path = os.path.join("screenshots", website, viewport, "design_docs", "sections", section_file)
        if not os.path.exists(section_path):
            raise FileNotFoundError(f"Section file not found: {section_path}")
        
        try:
            with open(section_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not read {section_path}: {e}")
            return ""

    async def generate_page_code(self, website: str, viewport: str):
        """Generate Shopify page code by combining sections in order."""
        try:
            # Get all section files in order
            section_files = self._find_section_files(website, viewport)
            if not section_files:
                raise ValueError("No section files found")
            
            # Get shopify code directory
            shopify_code_dir = os.path.join(self.screenshots_dir, website, viewport, "shopify_code")
            if not os.path.exists(shopify_code_dir):
                raise FileNotFoundError(f"Shopify code directory not found: {shopify_code_dir}")
            
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

            # Prepare section information
            sections_info = []
            for section_file in section_files:
                section_content = self._get_section_content(section_file, website, viewport)
                section_schema = self._get_section_schema(section_file, shopify_code_dir)
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

            # Create messages for Claude
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # Get code generation from Claude
            response = await shopify_llm.ainvoke(messages)
            
            # Save the generated code
            output_dir = os.path.join(self.screenshots_dir, website, viewport, "shopify_code")
            os.makedirs(output_dir, exist_ok=True)
            
            # Save the full response
            output_file = os.path.join(output_dir, "generated_page_code.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.content)
            
            # Extract and save individual files
            file_pattern = r"---\s*FILE:\s*([^\n]+)\s*TYPE:\s*([^\n]+)\s*CONTENT:\s*```(?:[^\n]*)\n([\s\S]*?)```\s*---"
            
            for match in re.finditer(file_pattern, response.content):
                file_path = match.group(1).strip()
                file_type = match.group(2).strip()
                file_content = match.group(3).strip()
                
                # Create full path
                full_path = os.path.join(output_dir, file_path.lstrip("/"))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Save file
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
            
            print(f"\n✅ Shopify page code generated and saved to: {output_dir}")
            print("\nGenerated files:")
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if not file.endswith("_code.txt"):
                        print(f"- {os.path.relpath(os.path.join(root, file), output_dir)}")
            
            return response.content
            
        except Exception as e:
            print(f"Error generating Shopify page code: {str(e)}")
            return None

async def main():
    # Check for required environment variables
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ Missing ANTHROPIC_API_KEY environment variable")
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate Shopify page code from design documentation")
    parser.add_argument("--website", required=True, help="Website directory name")
    parser.add_argument("--viewport", required=True, help="Viewport directory name")
    args = parser.parse_args()
    
    generator = ShopifyPageGenerator()
    
    try:
        await generator.generate_page_code(args.website, args.viewport)
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 