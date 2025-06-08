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

# Initialize Claude LLM with retry
design_llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.1,
    max_tokens=5000
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

class WebsiteDesignAnalyzer:
    def __init__(self, screenshots_dir="screenshots"):
        """Initialize the analyzer with screenshots directory."""
        self.screenshots_dir = screenshots_dir
        self.design_data = {}

    def _get_screenshot_paths(self):
        """Get all screenshot paths organized by website and viewport."""
        screenshot_paths = {}
        
        # Walk through the screenshots directory
        for website_dir in os.listdir(self.screenshots_dir):
            website_path = os.path.join(self.screenshots_dir, website_dir)
            if not os.path.isdir(website_path):
                continue
                
            screenshot_paths[website_dir] = {}
            
            # Get viewport directories
            for viewport_dir in os.listdir(website_path):
                viewport_path = os.path.join(website_path, viewport_dir)
                if not os.path.isdir(viewport_path):
                    continue
                    
                # Get all PNG screenshots in this viewport directory
                screenshots = glob.glob(os.path.join(viewport_path, "screenshot_*.png"))
                if screenshots:
                    screenshot_paths[website_dir][viewport_dir] = sorted(screenshots)
        
        return screenshot_paths

    def _get_image_dimensions(self, image_path):
        """Get the dimensions of an image."""
        with Image.open(image_path) as img:
            return img.size

    async def analyze_design(self, image_path):
        """Analyze a single screenshot to generate design documentation."""
        # Get image dimensions
        width, height = self._get_image_dimensions(image_path)
        
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Prepare the prompts
        system_prompt = """
        You are an expert Shopify theme developer and designer. Your task is to analyze a website screenshot and provide detailed documentation about its design and implementation.

        Provide a comprehensive analysis in a clear, structured format using markdown. Include code snippets where relevant to illustrate implementation approaches.

        Structure your analysis with these sections:

        # Design Overview
        - Overall style and aesthetic
        - Color scheme (with hex codes)
        - Typography (fonts, sizes, weights)
        - Layout and grid system
        - Spacing patterns

        # Section Analysis
        For each major section of the website:
        - Section name and purpose
        - Key elements and their arrangement
        - Design characteristics (colors, typography, spacing)
        - Implementation approach (HTML structure, CSS techniques, liquid )
        - Interactive elements and behaviors
        - Responsive considerations

        # Shopify Data Rendering
        - Product data handling (collections, products, variants)
        - Customer data integration
        - Cart and checkout integration
        - Collection templates and filtering
        - Dynamic content sections
        - Metafields usage
        - JSON templates and settings
        - Implementation code snippets with Liquid

        # Interactive Elements
        - Navigation menus
        - Buttons and CTAs
        - Forms and inputs
        - Hover states and animations
        - Product view information
        - Navigation menus (using Shopify menus)
        - Product cards and quick views
        - Collection filtering and sorting
        - Cart functionality
        - Forms (customer, contact, newsletter)
        - AJAX cart implementation
        - Implementation code snippets with Liquid, html, css and JavaScript

        # Responsive Design
        - Breakpoints and adaptation strategies
        - Mobile-first considerations
        - Layout changes at different viewports
        - Implementation approaches

        # Accessibility
        - Color contrast considerations
        - Keyboard navigation
        - Screen reader compatibility
        - ARIA attributes and semantic HTML
        - Shopify's accessibility guidelines
        - Form accessibility

        # Performance Optimization
        - Shopify image optimization (img_url filter)
        - Lazy loading implementation
        - Section rendering optimization
        - JavaScript performance
        - Code optimization tips
        - Shopify CDN usage

        # Implementation Guidelines
        - Shopify section architecture
        - Liquid template structure
        - CSS architecture (BEM, SMACSS)
        - JavaScript modules and organization
        - Reusable components and snippets
        - Required Shopify dependencies

        Include specific code snippets where they help illustrate the implementation. Use markdown code blocks with appropriate language tags:
        - `liquid` for Liquid templates
        - `json` for section schemas and settings
        - `javascript` for JavaScript code
        - `css` for styles

        Focus on Shopify-specific implementation details:
        1. Use Shopify's built-in filters and tags
        2. Follow Shopify's section architecture
        3. Implement proper data rendering patterns
        4. Follow Shopify's best practices for performance
        5. Ensure proper integration with Shopify's backend

        Be specific and detailed in your analysis, focusing on practical implementation details that would help a developer recreate this design within Shopify's theme architecture.
        """

        user_prompt = f"""
        Please analyze this website screenshot of a Shopify store and provide detailed design documentation.
        The image is {width}x{height} pixels.

        Focus on providing clear, actionable guidance that would help a developer recreate this design.
        Include specific code examples where they would be helpful.
        Consider modern web development best practices and techniques.

        Provide a comprehensive analysis covering:
        1. Visual design elements and their relationships
        2. Implementation approaches with code examples
        3. Responsive design strategies
        4. Accessibility requirements
        5. Performance optimizations
        6. Component architecture

        Pay special attention to:
        - How data is rendered using Liquid
        - Section schema structure
        - Theme settings organization
        - Dynamic content handling
        - Shopify-specific features and integrations
        """

        # Create messages for Claude
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                }
            ])
        ]

        try:
            # Get analysis from Claude with retry
            response = await design_llm.ainvoke(messages)
            return response.content
                
        except Exception as e:
            print(f"Error analyzing {image_path} after all retries: {str(e)}")
            return None

    async def analyze_all_screenshots(self):
        """Analyze all screenshots and save design documentation."""
        screenshot_paths = self._get_screenshot_paths()
        
        for website, viewports in screenshot_paths.items():
            self.design_data[website] = {}
            
            for viewport, screenshots in viewports.items():
                print(f"\nAnalyzing {website} - {viewport}")
                self.design_data[website][viewport] = []
                
                for screenshot_path in screenshots:
                    print(f"Processing {os.path.basename(screenshot_path)}...")
                    design_doc = await self.analyze_design(screenshot_path)
                    
                    if design_doc:
                        # Create design documentation directory
                        output_dir = os.path.join(
                            os.path.dirname(screenshot_path),
                            "design_docs"
                        )
                        os.makedirs(output_dir, exist_ok=True)
                        
                        # Save design documentation as markdown
                        base_filename = os.path.splitext(os.path.basename(screenshot_path))[0]
                        output_file = os.path.join(output_dir, f"{base_filename}_design.md")
                        
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(f"# Design Documentation for {base_filename}\n\n")
                            f.write(f"Viewport: {viewport}\n")
                            f.write(f"Image dimensions: {self._get_image_dimensions(screenshot_path)}\n\n")
                            f.write(design_doc)
                
                # Create a combined markdown file for this viewport
                combined_file = os.path.join(
                    self.screenshots_dir,
                    website,
                    viewport,
                    "combined_design.md"
                )
                
                with open(combined_file, "w", encoding="utf-8") as f:
                    f.write(f"# Combined Design Documentation for {website}\n\n")
                    f.write(f"Viewport: {viewport}\n\n")
                    
                    for screenshot_path in screenshots:
                        base_filename = os.path.splitext(os.path.basename(screenshot_path))[0]
                        f.write(f"## {base_filename}\n\n")
                        f.write(f"![Screenshot]({os.path.basename(screenshot_path)})\n\n")
                        
                        # Read and include individual design doc
                        doc_path = os.path.join(
                            os.path.dirname(screenshot_path),
                            "design_docs",
                            f"{base_filename}_design.md"
                        )
                        if os.path.exists(doc_path):
                            with open(doc_path, "r", encoding="utf-8") as doc_file:
                                f.write(doc_file.read())
                        f.write("\n---\n\n")

    async def analyze_single_screenshot(self, screenshot_path):
        """Analyze a single screenshot and save the design documentation."""
        if not os.path.exists(screenshot_path):
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")
            
        print(f"\nAnalyzing single screenshot: {screenshot_path}")
        
        # Get the website and viewport directories from the path
        path_parts = os.path.normpath(screenshot_path).split(os.sep)
        if len(path_parts) < 3:
            raise ValueError("Invalid screenshot path structure")
            
        website_dir = path_parts[-3]  # e.g., www_allbirds_com
        viewport_dir = path_parts[-2]  # e.g., default_1920x1080
        
        # Create design documentation directory
        output_dir = os.path.join(os.path.dirname(screenshot_path), "design_docs")
        os.makedirs(output_dir, exist_ok=True)
        
        # Analyze the screenshot
        design_doc = await self.analyze_design(screenshot_path)
        
        if design_doc:
            # Save design documentation as markdown
            base_filename = os.path.splitext(os.path.basename(screenshot_path))[0]
            output_file = os.path.join(output_dir, f"{base_filename}_design.md")
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# Design Documentation for {base_filename}\n\n")
                f.write(f"Website: {website_dir}\n")
                f.write(f"Viewport: {viewport_dir}\n")
                f.write(f"Image dimensions: {self._get_image_dimensions(screenshot_path)}\n\n")
                f.write(design_doc)
            
            print(f"\n✅ Design documentation saved to: {output_file}")
            print("\nDocumentation includes:")
            print("- Design overview and analysis")
            print("- Section-by-section breakdown")
            print("- Implementation guidelines")
            print("- Code snippets and examples")
            
            return design_doc
        
        return None

async def main():
    # Check for required environment variables
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ Missing ANTHROPIC_API_KEY environment variable")
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate design documentation from website screenshots")
    parser.add_argument("--test", help="Path to a single screenshot to analyze")
    args = parser.parse_args()
    
    analyzer = WebsiteDesignAnalyzer()
    
    if args.test:
        # Test mode: analyze single screenshot
        try:
            await analyzer.analyze_single_screenshot(args.test)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    else:
        # Full mode: analyze all screenshots
        await analyzer.analyze_all_screenshots()
        print("\n✅ Design documentation generation complete!")

if __name__ == "__main__":
    asyncio.run(main())
