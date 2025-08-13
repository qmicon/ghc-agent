# Offer Page Generator

This tool helps generate Shopify offer pages by analyzing requirements and creating implementation plans.

## Setup

1. Create and activate a Python virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
ANTHROPIC_API_KEY=your_api_key_here
```

## Usage

1. Create your initial requirements:
   - Create a file named `simple_offer_requirement.txt`
   - Add your basic offer page requirements in this file

2. Enhance your requirements:
```bash
python enhance_prompt.py
```
This will generate `enhanced_prompt.txt` with detailed requirements. Review and copy the content to `offer_requirements_prompt.txt`.

3. Generate code examples:
```bash
python generate_examples_from_template.py
```
This script:
- Reads from `offer_requirements_prompt.txt`
- Finds relevant examples from `example_components/` and `dataset/`
- Creates `examples.txt` with implementation examples and UI component examples

4. Generate the offer plan (multi-file plan recommended):
```bash
python generate_offer_plan_claude.py
```
This script:
- Reads from `offer_requirements_prompt.txt`
- Uses `examples.txt` if available
- Fetches your Shopify store data
- Generates a detailed implementation plan in `offer_plan_claude.txt`
- The plan includes code for multiple files (sections, snippets, templates)

5. Convert the plan into a single Liquid template (optional but recommended for deployment as one file):
```bash
python convert_plan_to_one_liquid_claude.py
```
This script:
- Reads the multi-file plan from `offer_plan_claude.txt`
- Reads the grounding requirements from `offer_requirements_prompt.txt`
- Instructs the model to consolidate all code into one file
- Writes the single-file implementation to `one_page_offer_from_plan.txt`

Optional environment overrides:
```bash
PLAN_PATH=offer_plan_claude.txt OUTPUT_PATH=one_page_offer_from_plan.txt python convert_plan_to_one_liquid_claude.py
```

6. Save the implementation:
```bash
# Save from converted single-file plan (default)
python save_implementations.py

# Save from the original multi-file plan
python save_implementations.py --source main
```
This script extracts code blocks and writes files under `claude_workspace/`:
- Default mode (converted): reads `one_page_offer_from_plan.txt` and saves a single `templates/page.offer.liquid` file.
- Main mode: reads `offer_plan_claude.txt` and saves all referenced files (sections, snippets, templates) as defined in the plan.

6. Align template styling (optional):
```bash
python align_template_styling.py --website your-store.com --template path/to/template.liquid --output-dir styled_templates
```
This script:
- Analyzes a product page from your Shopify store to extract design elements
- Takes screenshots of each section and extracts HTML code
- Uses LLM to analyze design patterns, colors, typography, and layout
- Generates a design consistency document
- Applies styling changes to your template to match the product page design
- Saves the styled template to the output directory

**Arguments:**
- `--website`: Your Shopify store domain (e.g., marsghc.com)
- `--template`: Path to the template file you want to style
- `--output-dir`: Directory to save the final styled template
- `--int-dir`: Intermediate files directory (default: styling_int_files)
- `--log-dir`: Log files directory (default: logs)

**Requirements:**
- `ANTHROPIC_API_KEY` environment variable must be set
- Requires `playwright` for screenshot capture
- Requires `PIL` for image processing

**Output:**
- Screenshots and HTML files in `styling_int_files/screenshots/`
- Design analysis in `styling_int_files/design_elements/`
- Design consistency document in `styling_int_files/design_consistency.md`
- Suggested edits in `styling_int_files/suggested_edits.txt`
- Final styled template in your specified output directory
- Detailed logs in the logs directory

## Directory Structure

```
.
├── dataset/                    # Example code dataset
├── example_components/         # Example UI components
├── venv/                      # Python virtual environment
├── .env                       # Environment variables
├── requirements.txt           # Python package requirements
├── simple_offer_requirement.txt  # Initial requirements
├── enhanced_prompt.txt        # Enhanced requirements
├── offer_requirements_prompt.txt  # Final requirements
├── examples.txt              # Generated code examples
├── offer_plan_claude.txt     # Implementation plan
├── generate_examples_from_template.py  # Generate examples
├── generate_offer_plan_claude.py       # Generate multi-file plan
├── convert_plan_to_one_liquid_claude.py # Convert plan to single Liquid file
├── enhance_prompt.py         # Requirements enhancement
├── save_implementations.py   # Save files from plan
└── align_template_styling.py # Align template styling with store design
```

## Notes

- Update `shopify_url` in `generate_offer_plan_claude.py` to your store's URL.
- Environment variables:
  - For both generation scripts, you'll need `ANTHROPIC_API_KEY` in your `.env` file
- The flow uses the same examples from `examples.txt` if available.
- Recommended flow:
  1. Generate a multi-file plan in `offer_plan_claude.txt`
  2. Convert it to a one-file template into `one_page_offer_from_plan.txt`
  3. Save implementations with `save_implementations.py` (default uses the converted plan)
- If you prefer to create multiple Liquid files instead of a single file, run `save_implementations.py --source main` to save from the original multi-file plan.

# Code Editing Workflow

This section describes the workflow for making edits to the Shopify codebase using the editing tools.

## Overview

The editing workflow consists of two main scripts:
1. `generate_edits.py` - Analyzes edit requirements and generates suggested edits
2. `apply_edits.py` - Applies the suggested edits to create modified files

## Setup

1. Create an `edit_prompt.txt` file with your editing requirements
2. Ensure your `ANTHROPIC_API_KEY` environment variable is set
3. Make sure your codebase is in the `claude_workspace` directory

## Usage

### Step 1: Generate Suggested Edits

1. Write your editing requirements in `edit_prompt.txt`
2. Run the edit generation script:
   ```bash
   python generate_edits.py
   ```
3. Review the generated `suggested_edits.txt` file, which will contain:
   - A list of suggested changes
   - Each change includes:
     - File path
     - Original code (SEARCH)
     - New code (REPLACE)
     - Explanation of the changes

### Step 2: Apply the Edits

1. Review the suggested edits in `suggested_edits.txt`
2. Run the apply edits script:
   ```bash
   python apply_edits.py
   ```
3. The script will:
   - Create a new `claude_workspace_edits` directory
   - Copy all files from `claude_workspace`
   - Apply the suggested edits to files in the edits directory
   - Leave the original workspace untouched
4. Review the modified files in `claude_workspace_edits`

## Directory Structure

```
.
├── claude_workspace/           # Original codebase
├── claude_workspace_edits/     # Modified files (created by apply_edits.py)
├── edit_prompt.txt            # Your editing requirements
├── suggested_edits.txt        # Generated edit suggestions
├── generate_edits.py          # Script to generate edit suggestions
└── apply_edits.py            # Script to apply the edits
```

## Notes

- The editing workflow preserves your original codebase by creating a separate directory for modified files
- Each edit in `suggested_edits.txt` follows the code editing diff format (see [diff format documentation](https://aider.chat/docs/more/edit-formats.html#diff))
- The apply script handles whitespace differences and provides detailed feedback about each edit
- If an edit fails, check the error message for details about what went wrong
- You can safely delete the `claude_workspace_edits` directory to start over
