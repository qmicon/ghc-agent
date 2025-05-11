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

1. Create your offer requirements:
   - Create a file named `offer_requirements_prompt.txt`
   - Add your offer page requirements in this file
   - Example requirements:
     ```
     Create a new custom page template titled "Buy 3 for 99" with the following layout and behavior:
     
     1. Banner Section
     Full-width banner image at the top of the page
     Include a heading: "Pick Any 3 Products for ₹99"
     Optional subtext for promotion details
     
     2. Product Grid Section
     Display a grid of selectable products
     Each product should have an image, name, and "Select" button
     When a product is selected, change the button to "Selected" and visually highlight it
     Only allow up to 3 products to be selected
     
     3. Selected Products Section (Fixed at Bottom)
     Sticky section at the bottom of the page
     Show 3 empty slots initially
     As the user selects products, fill the slots with the selected product images/names
     Include a "Checkout for ₹99" button
     The button remains disabled until exactly 3 products are selected
     ```

2. Generate code examples:
```bash
python generate_examples_from_template.py
```
This will create `examples.txt` with relevant code examples:
- Implementation examples from the `dataset/` directory.
- UI component examples from the `example_components/` directory.

3. Generate implementation plan:
```bash
python generate_offer_plan_claude.py
```
This will create `offer_plan_claude.txt` with a detailed implementation plan.

4. Save implementations:
```bash
python save_implementations.py
```
This will create the actual implementation files based on the plan and create a claude workspace directory

## Directory Structure

```
.
├── dataset/                    # Example code dataset for full offer implementations
│   ├── desc-buy-x-for-y/      # Descriptive buy X for Y examples
│   └── simple-buy-x-for-y/    # Simple buy X for Y examples
├── example_components/         # Example UI components (sections, snippets)
├── venv/                      # Python virtual environment
├── .env                       # Environment variables
├── requirements.txt           # Python package requirements
├── offer_requirements_prompt.txt  # Your offer requirements
├── examples.txt              # Generated code examples
├── offer_plan_claude.txt     # Generated implementation plan
├── generate_examples_from_template.py      # Example generation script
├── generate_offer_plan_claude.py  # Plan generation script
└── save_implementations.py   # Implementation saving script
```

## Notes

- Make sure to update `offer_requirements_prompt.txt` with your specific requirements before running the scripts
- The generated implementation will be saved in the appropriate Shopify theme directory structure
- Check the generated files for any necessary adjustments before deploying
