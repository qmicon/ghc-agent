# Theme Generator

A robust pipeline for generating Shopify themes from website screenshots, orchestrated by just two main scripts. This toolchain is designed for developers who want to automate theme creation, track all intermediate steps, and ensure reproducibility and traceability.

## Setup

1. **Clone the repository and change to the theme_generator directory:**
   ```bash
   cd theme_generator
   ```

2. **Create and activate a Python virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Create .env file in the parent directory
   ANTHROPIC_API_KEY=your_api_key_here
   ```

5. **Ensure the reference Dawn theme is present:**
   - The `dawn-main/` directory must be present in `theme_generator/`. It will be copied into each new project as the starting point for theme code.

## Usage

The workflow is streamlined into two main commands:

### 1. Create a Project Folder

This script creates a new project folder, copies the reference Dawn theme, and sets up the required structure for intermediate files and theme code.

```bash
python create_theme_project.py
```
- Prints the new project folder name (e.g., `theme_abc12345`).
- The folder is created in `theme-projects/`.

### 2. Run the Clone Script

This script orchestrates the entire pipeline: screenshots, design doc generation, section planning, code example extraction, section and page code generation, and checkpointing.

```bash
python clone_theme_from_website.py <website> <project_folder> <page_type> --viewport <viewport>
```
- `<website>`: The website domain (e.g., `marsghc.com`)
- `<project_folder>`: The folder created in step 1
- `<page_type>`: The type of page to clone (e.g., `Home`, `Collection`, `Product`, `AllBlogs`, `SingleBlog`)
- `--viewport`: (Optional) `mobile` or `desktop` (default: `mobile`)

**Example:**
```bash
python clone_theme_from_website.py marsghc.com theme_10836f00 Home
```

#### What Happens When You Run the Clone Script?
- The script resolves the canonical URL for the page type.
- All intermediate files and outputs are created in `theme-projects/<project_folder>/intermediate_files/<url>/<viewport>/`.
- The generated Shopify theme code is saved in `theme-projects/<project_folder>/theme_code/sections/` and `/templates/`.
- A `checkpoint.json` is created to allow resuming from the last successful step if interrupted.
- All section files in `theme_code/sections/` are suffixed with a unique epoch to avoid collisions across runs. The template JSON is updated to reference these unique section types.

#### Multiple Runs and Checkpointing
- If you run the clone script again with the same arguments, it will **resume from the last successful step** using `checkpoint.json`.
- If you change the website, page type, or viewport, a new set of intermediate files and code will be generated.
- The canonical theme code in `theme_code/sections/` and `theme_code/templates/` will always reflect the latest run, with unique section file names to avoid collisions.

## Directory Structure

```
theme_generator/
├── create_theme_project.py         # Creates a new project folder and copies dawn-main
├── clone_theme_from_website.py     # Main pipeline/orchestration script
├── dawn-main/                      # Reference Shopify Dawn theme (copied into each new project)
├── dataset/                        # Example code datasets
├── requirements.txt
├── ... (other utility scripts, not run directly)
└── theme-projects/
    └── <project_folder>/
        ├── intermediate_files/
        │   └── <url>/<viewport>/
        │       ├── screenshots/
        │       ├── design_docs/
        │       ├── section_design_plans/
        │       │   └── sections/
        │       ├── theme_examples/
        │       ├── code_changes/
        │       │   ├── sections/
        │       │   └── templates/
        │       └── checkpoint.json
        └── theme_code/
            ├── sections/      # Final Shopify section files (with unique epoch suffix)
            └── templates/     # Final Shopify page templates (with updated section type references)
```

## Developer Notes

- **You only need to run `create_theme_project.py` and `clone_theme_from_website.py`.** All other scripts are orchestrated automatically.
- The pipeline is fully checkpointed. If a step fails, fix the issue and rerun the clone script; it will resume from the last successful step.
- All intermediate files are kept for traceability and debugging.
- The canonical theme code is always up to date and collision-free, with unique section file names for each run.
- You can run the clone script multiple times for the same or different websites, page types, or viewports.
- The `dawn-main/` directory is used as the base for all new projects. Update it if you want to change the starting point for theme code.
- The `dataset/` directory contains example code used for code generation.
- The `checkpoint.json` in each run's intermediate directory records which steps have completed.

## Error Handling

- Each step is checkpointed; if a step fails, you can rerun the script and it will resume from the last successful step.
- Failed steps are logged to the console.
- Review the generated files to ensure they meet your requirements.

## Best Practices

1. Start with a clear target website and page type
2. Use a unique project folder for each theme project
3. Review the generated design documentation and code in the intermediate files if needed
4. Test the generated Shopify theme in a development store
5. Rerun the clone script as needed to resume or update the theme code 