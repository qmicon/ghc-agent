import os
import sys
import argparse
import subprocess
import glob
import shutil
import base64
import asyncio
import logging
from datetime import datetime
from pathlib import Path
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

# Configure logging
def setup_logging(log_dir="logs"):
    """Setup logging configuration."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"align_template_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger

# Initialize Claude LLM with retry
design_llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.1,
    max_tokens=20000
).with_retry(
    stop_after_attempt=5,
    wait_exponential_jitter=True,
    retry_if_exception_type=(Exception,),
    exponential_jitter_params={
        "initial": 5,
        "max": 60,
        "exp_base": 2,
        "jitter": 0.1
    }
)

def analyze_design_element(image_path, html_path, logger):
    """Analyze a single screenshot and HTML to extract design elements."""
    logger.info(f"Starting analysis of {os.path.basename(image_path)}")
    
    try:
        # Read and encode image
        logger.debug(f"Reading and encoding image: {image_path}")
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        logger.debug(f"Image encoded successfully, size: {len(image_data)} chars")
        
        # Read HTML content
        logger.debug(f"Reading HTML content: {html_path}")
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        logger.debug(f"HTML content read, size: {len(html_content)} chars")
        
        # Get image dimensions
        from PIL import Image
        with Image.open(image_path) as img:
            width, height = img.size
        logger.debug(f"Image dimensions: {width}x{height}")
    except Exception as e:
        logger.error(f"Error reading files for {image_path}: {str(e)}")
        raise
    
    system_prompt = """
    You are an expert Shopify theme developer and designer. Analyze the screenshot and HTML to extract important design elements and their purposes.
    
    Focus on:
    1. CSS styles and design patterns
    2. Color schemes and typography
    3. Layout structures and spacing
    4. Interactive elements and their styling
    5. Responsive design considerations
    
    Return a JSON object with:
    - styles: Array of important CSS styles found
    - colors: Array of color codes used
    - typography: Font families, sizes, weights
    - layout: Layout patterns and structures
    - description: What this section is used for
    - interactive_elements: Any interactive components
    """
    
    user_prompt = f"""
    Please analyze this website section screenshot and HTML to extract design elements.
    Image dimensions: {width}x{height} pixels
    
    HTML Content:
    {html_content}
    
    Provide a comprehensive analysis of the design elements and their purposes.
    """
    
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
        logger.info(f"Sending analysis request to LLM for {os.path.basename(image_path)}")
        response = design_llm.invoke(messages)
        logger.info(f"LLM response received for {os.path.basename(image_path)}")
        
        # Try to parse as JSON, fallback to structured text
        try:
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group())
                logger.info(f"Successfully parsed JSON response for {os.path.basename(image_path)}")
                return parsed_json
        except Exception as json_error:
            logger.warning(f"Failed to parse JSON for {os.path.basename(image_path)}: {str(json_error)}")
        
        # Fallback: return structured data
        logger.info(f"Using fallback structured data for {os.path.basename(image_path)}")
        return {
            'image': image_path,
            'html': html_path,
            'styles': ['/* Extracted from analysis */'],
            'description': response.content[:500] + '...' if len(response.content) > 500 else response.content,
            'colors': [],
            'typography': {},
            'layout': {},
            'interactive_elements': []
        }
    except Exception as e:
        logger.error(f"Error analyzing {image_path}: {str(e)}")
        return {
            'image': image_path,
            'html': html_path,
            'styles': [],
            'description': f'Error during analysis: {str(e)}',
            'colors': [],
            'typography': {},
            'layout': {},
            'interactive_elements': []
        }

def generate_design_consistency(design_elements, logger):
    """Generate design consistency document from all design elements."""
    logger.info(f"Starting design consistency generation for {len(design_elements)} elements")
    
    system_prompt = """
    You are an expert Shopify theme developer. Analyze all the design elements from different sections and create a comprehensive design consistency document.
    
    Create a markdown document that includes:
    1. Overall Design System
    2. Color Palette and Usage
    3. Typography Guidelines
    4. Layout Patterns
    5. Component Guidelines
    6. Interactive Element Standards
    7. Responsive Design Rules
    
    Focus on creating a cohesive design system that can be applied consistently across the theme.
    """
    
    # Prepare design elements summary
    logger.debug("Preparing design elements summary")
    elements_summary = []
    for i, element in enumerate(design_elements, 1):
        elements_summary.append(f"Section {i}: {element.get('description', 'No description')}")
        if element.get('styles'):
            elements_summary.append(f"Styles: {element.get('styles')}")
        if element.get('colors'):
            elements_summary.append(f"Colors: {element.get('colors')}")
        elements_summary.append("---")
    
    user_prompt = f"""
    Based on the following design elements from different sections of the website, create a comprehensive design consistency document:
    
    {chr(10).join(elements_summary)}
    
    Create a detailed design system that captures the visual language and can be used to style other templates consistently.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        logger.info("Sending design consistency request to LLM")
        response = design_llm.invoke(messages)
        logger.info("Design consistency document generated successfully")
        return response.content
    except Exception as e:
        logger.error(f"Error generating design consistency: {str(e)}")
        return "# Design Consistency Document\n\nError generating design consistency document."

def generate_edits_for_template(template_code, design_consistency_doc, edit_rules, logger):
    """Generate edits for template based on design consistency document."""
    logger.info("Starting template edit generation")
    logger.debug(f"Template code size: {len(template_code)} chars")
    logger.debug(f"Design consistency doc size: {len(design_consistency_doc)} chars")
    
    system_prompt = """
    You are a Shopify theme developer specialized in making precise code edits.
    Analyze the design consistency document and the current template to suggest specific styling edits.

    Your task is to generate edits in the following format:

    ```
    <<<<<<< SEARCH
    [exact content to replace]
    =======
    [new content to insert]
    >>>>>>> REPLACE
    ```

    Critical rules for SEARCH/REPLACE blocks:
    1. SEARCH content must match exactly what's in the file:
       - Match character-for-character including whitespace, indentation, line endings
       - Include all comments, docstrings, etc.
    2. SEARCH/REPLACE blocks will ONLY replace the first match occurrence:
       - Include multiple unique SEARCH/REPLACE blocks if you need to make multiple changes
       - Include just enough lines in each SEARCH section to uniquely match each set of lines
       - List multiple SEARCH/REPLACE blocks in the order they appear in the file
    3. Keep SEARCH/REPLACE blocks concise:
       - Break large blocks into smaller ones that each change a small portion
       - Include just the changing lines and a few surrounding lines for uniqueness
       - Do not include long runs of unchanging lines
       - Each line must be complete (never truncate lines)
    4. Special operations:
       - To move code: Use two SEARCH/REPLACE blocks (delete + insert)
       - To delete code: Use empty REPLACE section

    Focus ONLY on styling changes (CSS, colors, typography, spacing) based on the design consistency document.
    Do not change the structure or functionality of the template.
    """
    
    user_prompt = f"""
    Design Consistency Document:
    {design_consistency_doc}
    
    Current Template Code:
    {template_code}
    
    Edit Rules:
    {edit_rules}
    
    Please suggest specific styling edits to align the template with the design consistency document.
    Focus only on CSS styling changes, colors, typography, and spacing.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        logger.info("Sending template edit request to LLM")
        response = design_llm.invoke(messages)
        logger.info("Template edits generated successfully")
        logger.debug(f"Generated edits size: {len(response.content)} chars")
        return response.content
    except Exception as e:
        logger.error(f"Error generating edits: {str(e)}")
        return "# Error generating edits\n\nCould not generate edits due to an error."

def apply_edits_to_template(template_path, edits, output_path, logger):
    """Apply edits to template using SEARCH/REPLACE format."""
    logger.info(f"Applying edits to template: {os.path.basename(template_path)}")
    
    try:
        # Read template content
        logger.debug(f"Reading template file: {template_path}")
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug(f"Template content size: {len(content)} chars")
        
        # Parse SEARCH/REPLACE blocks
        import re
        pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
        matches = list(re.finditer(pattern, edits, re.DOTALL))
        logger.info(f"Found {len(matches)} SEARCH/REPLACE blocks to apply")
        
        applied_count = 0
        for i, match in enumerate(matches, 1):
            search = match.group(1)
            replace = match.group(2)
            logger.debug(f"Processing edit {i}/{len(matches)}")
            logger.debug(f"Search content length: {len(search)} chars")
            logger.debug(f"Replace content length: {len(replace)} chars")
            
            if search in content:
                content = content.replace(search, replace, 1)  # Replace only first occurrence
                applied_count += 1
                logger.info(f"Successfully applied edit {i}")
            else:
                logger.warning(f"Search content not found in template for edit {i}")
        
        # Write updated content
        logger.debug(f"Writing updated template to: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Template edits completed. Applied {applied_count}/{len(matches)} edits")
        return applied_count
        
    except Exception as e:
        logger.error(f"Error applying edits to template: {str(e)}")
        raise


def main():
    # Check for required environment variable
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")

    parser = argparse.ArgumentParser(description="Align template styling with product page design.")
    parser.add_argument('--website', required=True, help='Canonical website domain (e.g. marsghc.com)')
    parser.add_argument('--template', required=True, help='Path to the one-page template liquid file')
    parser.add_argument('--output-dir', required=True, help='Directory to save the final edited template')
    parser.add_argument('--int-dir', default='styling_int_files', help='Intermediate files directory')
    parser.add_argument('--log-dir', default='logs', help='Directory for log files')
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.log_dir)
    logger.info("=" * 60)
    logger.info("Starting template styling alignment process")
    logger.info("=" * 60)

    website = args.website
    template_path = args.template
    output_dir = args.output_dir
    int_dir = args.int_dir
    
    logger.info(f"Website: {website}")
    logger.info(f"Template: {template_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Intermediate directory: {int_dir}")
    
    screenshots_dir = os.path.join(int_dir, 'screenshots')
    design_elements_dir = os.path.join(int_dir, 'design_elements')
    
    # Create directories
    logger.info("Creating directories...")
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(design_elements_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    logger.info("Directories created successfully")

    # 1. Get product page URL
    logger.info("Step 1: Getting product page URL...")
    try:
        result = subprocess.run([
            sys.executable, 'theme_generator/get_shopify_page_url_from_sitemap.py', website, 'Product'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error getting product page URL: {result.stderr}")
            sys.exit(1)
        
        url_line = next((l for l in result.stdout.splitlines() if l.startswith('URL for')), None)
        if not url_line:
            logger.error("Could not parse product page URL from output")
            logger.debug(f"Subprocess output: {result.stdout}")
            sys.exit(1)
        
        product_url = url_line.split(':', 1)[-1].strip()
        logger.info(f"Product page URL: {product_url}")
        
    except Exception as e:
        logger.error(f"Exception while getting product page URL: {str(e)}")
        sys.exit(1)

    # 2. Take screenshots and element HTML
    logger.info("Step 2: Taking screenshots and saving element HTML...")
    try:
        # Extract domain from product URL for the screenshot script
        from urllib.parse import urlparse
        parsed_url = urlparse(product_url)
        domain = parsed_url.netloc
        logger.debug(f"Extracted domain: {domain}")
        
        logger.info(f"Running screenshot script for domain: {domain}")
        result = subprocess.run([
            sys.executable, 'theme_generator/take_shopify_screenshot.py', domain, 'desktop',
            '--output-dir', screenshots_dir, '--save-selector-code'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error taking screenshots: {result.stderr}")
            sys.exit(1)
        
        logger.info("Screenshots captured successfully")
        logger.debug(f"Screenshot script output: {result.stdout}")
        
    except Exception as e:
        logger.error(f"Exception while taking screenshots: {str(e)}")
        sys.exit(1)

    # 3. Analyze each screenshot + HTML
    logger.info("Step 3: Analyzing screenshots and HTML for design elements...")
    try:
        screenshots = sorted(glob.glob(os.path.join(screenshots_dir, '*.png')))
        logger.info(f"Found {len(screenshots)} screenshots to analyze")
        
        design_elements = []
        for i, screenshot_path in enumerate(screenshots, 1):
            logger.info(f"Analyzing screenshot {i}/{len(screenshots)}: {os.path.basename(screenshot_path)}")
            
            base = os.path.splitext(os.path.basename(screenshot_path))[0]
            html_path = os.path.join(screenshots_dir, base + '.txt')
            
            if not os.path.exists(html_path):
                logger.warning(f"No HTML file found for {base}, skipping...")
                continue
            
            try:
                analysis = analyze_design_element(screenshot_path, html_path, logger)
                design_elements.append(analysis)
                
                # Save each analysis
                analysis_file = os.path.join(design_elements_dir, base + '.json')
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2)
                logger.debug(f"Saved analysis to: {analysis_file}")
                
            except Exception as e:
                logger.error(f"Error analyzing {screenshot_path}: {str(e)}")
                continue
        
        logger.info(f"Successfully analyzed {len(design_elements)} sections")
        
    except Exception as e:
        logger.error(f"Exception during screenshot analysis: {str(e)}")
        sys.exit(1)

    # 4. Generate design consistency doc
    logger.info("Step 4: Generating design consistency doc...")
    try:
        design_consistency_doc = generate_design_consistency(design_elements, logger)
        consistency_path = os.path.join(int_dir, 'design_consistency.md')
        
        with open(consistency_path, 'w', encoding='utf-8') as f:
            f.write(design_consistency_doc)
        
        logger.info(f"Design consistency doc saved to {consistency_path}")
        logger.debug(f"Consistency doc size: {len(design_consistency_doc)} chars")
        
    except Exception as e:
        logger.error(f"Exception during design consistency generation: {str(e)}")
        sys.exit(1)

    # 5. Generate edits for template
    logger.info("Step 5: Generating edits for template...")
    try:
        logger.debug(f"Reading template file: {template_path}")
        with open(template_path, 'r', encoding='utf-8') as f:
            template_code = f.read()
        logger.debug(f"Template code size: {len(template_code)} chars")
        
        # Get edit rules from generate_edits.py
        logger.debug("Reading edit rules from generate_edits.py")
        with open('generate_edits.py', 'r', encoding='utf-8') as f:
            edit_rules = f.read()
        logger.debug(f"Edit rules size: {len(edit_rules)} chars")
        
        edits = generate_edits_for_template(template_code, design_consistency_doc, edit_rules, logger)
        edits_path = os.path.join(int_dir, 'suggested_edits.txt')
        
        with open(edits_path, 'w', encoding='utf-8') as f:
            f.write(edits)
        
        logger.info(f"Edits saved to {edits_path}")
        logger.debug(f"Generated edits size: {len(edits)} chars")
        
    except Exception as e:
        logger.error(f"Exception during edit generation: {str(e)}")
        sys.exit(1)

    # 6. Apply edits
    logger.info("Step 6: Applying edits to template...")
    try:
        output_template_path = os.path.join(output_dir, os.path.basename(template_path))
        applied_count = apply_edits_to_template(template_path, edits, output_template_path, logger)
        logger.info(f"Final edited template saved to {output_template_path}")
        
    except Exception as e:
        logger.error(f"Exception during edit application: {str(e)}")
        sys.exit(1)

    # 7. Print summary
    logger.info("=" * 60)
    logger.info("PROCESS COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info("SUMMARY:")
    logger.info(f"  Product page URL: {product_url}")
    logger.info(f"  Screenshots and HTML: {screenshots_dir}")
    logger.info(f"  Design elements: {design_elements_dir}")
    logger.info(f"  Design consistency doc: {consistency_path}")
    logger.info(f"  Suggested edits: {edits_path}")
    logger.info(f"  Final template: {output_template_path}")
    logger.info(f"  Edits applied: {applied_count}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main() 