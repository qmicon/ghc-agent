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

4. Generate the offer page (choose one approach):

   a. Multi-file approach (recommended for complex pages):
   ```bash
   python generate_offer_plan_claude.py
   ```
   This script:
   - Reads from `offer_requirements_prompt.txt`
   - Uses `examples.txt` if available
   - Fetches your Shopify store data
   - Generates a detailed implementation plan in `offer_plan_claude.txt`
   - The plan includes code for multiple files (sections, snippets, templates)

   b. Single-file approach (simpler pages):
   ```bash
   python generate_one_page_liquid_claude.py
   ```
   This script:
   - Reads from `offer_requirements_prompt.txt`
   - Uses `examples.txt` if available
   - Fetches your Shopify store data
   - Generates a detailed implementation plan in `offer_plan_claude.txt`
   - The plan includes code for a single template file

5. Save the implementation:
```bash
python save_implementations.py
```
This script reads `offer_plan_claude.txt` and creates the files according to the plan in the claude workspace directory.

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
├── generate_offer_plan_claude.py       # Multi-file approach
├── generate_one_page_liquid_claude.py  # Single-file approach
├── enhance_prompt.py         # Requirements enhancement
└── save_implementations.py   # Save files from plan
```

## Notes

- **Important**: Update `shopify_url` in both `generate_offer_plan_claude.py` and `generate_one_page_liquid_claude.py` to your store's URL
- For both generation scripts, you'll need `AZURE_OPENAI_API_KEY` in your `.env` file
- Both approaches use the same examples from `examples.txt` if available
- Both approaches follow the same process:
  1. Generate a plan in `offer_plan_claude.txt`
  2. Use `save_implementations.py` to create the files
- The only difference is what files they generate in the plan:
  - Multi-file approach: Creates separate files for sections, snippets, and templates
  - Single-file approach: Creates a single template file
- The multi-file approach is recommended for complex pages as it provides more flexibility
- The single-file approach is simpler but may be less flexible for complex requirements

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
