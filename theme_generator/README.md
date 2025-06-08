# Theme Generator

A suite of tools for generating Shopify themes from website screenshots. This toolchain helps analyze website designs and convert them into production-ready Shopify themes.

## Setup

1. Change to the theme_generator directory:
```bash
cd theme_generator
```

2. Create and activate a Python virtual environment in the parent directory:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Create .env file in the parent directory
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

The theme generation process consists of several steps, each handled by a specific script. Here's the workflow:

### 1. Take Screenshots

Capture screenshots of the target website for analysis:

```bash
python take_screenshot.py www.example.com
```

This will:
- Take full-page screenshots of the website
- Save them in `screenshots/www_example_com/default_1920x1080/`
- Create a metadata.json file with screenshot information

### 2. Generate Design Documentation

Analyze the screenshots to create detailed design documentation:

```bash
python generate_prompt_from_image.py
```

This will:
- Analyze the screenshots and generate design documentation
- Save documentation in `screenshots/www_example_com/default_1920x1080//design_docs/`
- Create markdown files with design analysis and implementation notes

### 3. Generate Section Design Plans

Create detailed implementation plans for each section:

```bash
python generate_section_design_plan.py --website www_example_com --viewport default_1920x1080
```

This will:
- Generate implementation plans for sections
- Save plans in `screenshots/www_example_com/default_1920x1080/design_docs/sections/`
- Create numbered markdown files (e.g., `01-hero-section.md`)

### 4. Generate Theme Examples

Find relevant code examples for implementation:

```bash
python generate_theme_examples.py --website www_example_com --viewport default_1920x1080
```

This will:
- Analyze section designs and find relevant examples
- Search through the dataset directory for matching patterns
- Save examples in `screenshots/www_example_com/default_1920x1080/design_docs/examples/`
- Create numbered example files (e.g., `01-examples.txt`)

### 5. Generate Shopify Sections

Create the actual Shopify section files:

```bash
python generate_shopify_section.py --website www_example_com --viewport default_1920x1080
```

This will:
- Generate Shopify section files from the design plans
- Use examples to inform the implementation
- Save files in `screenshots/www_example_com/default_1920x1080/shopify_code/`
- Create `.liquid` files with proper schema and implementation

### 6. Generate Shopify Page

Combine all sections into a complete page:

```bash
python generate_shopify_page.py --website www_example_com --viewport default_1920x1080
```

This will:
- Combine all generated sections into a complete page
- Create the page template and settings
- Save files in `screenshots/www_example_com/default_1920x1080/shopify_code/templates/`
- Generate `page.custom.json`

## Directory Structure

```
theme_generator/
├── dataset/                    # Example code dataset
├── screenshots/               # Generated screenshots and code
│   └── [website]/            # Website-specific directory
│       └── [viewport]/       # Viewport-specific directory
│           ├── design_docs/  # Design documentation
│           │   ├── sections/ # Section design plans
│           │   └── examples/ # Implementation examples
│           └── shopify_code/ # Generated Shopify files
│               └── templates/# Page templates
├── requirements.txt          # Python package requirements
├── take_screenshot.py       # Screenshot capture tool
├── generate_prompt_from_image.py    # Design analysis
├── generate_section_design_plan.py  # Section planning
├── generate_theme_examples.py       # Example generation
├── generate_shopify_section.py      # Section generation
└── generate_shopify_page.py         # Page generation
```

## Notes

- All scripts support processing either a single section (using `--section`) or all sections
- The `--section` argument is optional; if not provided, all sections will be processed
- Each script builds on the output of the previous script in the workflow
- The generated Shopify code follows best practices and includes:
  - Proper section schemas
  - Responsive design
  - Accessibility features
  - Performance optimizations
- The dataset directory contains example code that informs the generation process
- All generated files are saved in the screenshots directory for easy review and testing

## Error Handling

- Each script includes error handling and validation
- Failed sections are logged but don't stop the entire process
- Check the console output for warnings and errors
- Review the generated files to ensure they meet your requirements

## Best Practices

1. Start with a clear target website
2. Review the generated design documentation
3. Check the section plans before generating code
4. Test the generated Shopify theme in a development store
5. Make adjustments as needed using the editing workflow 