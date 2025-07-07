# Usage: python clone_theme_from_website.py <website> <project_folder> <page_type> [--viewport mobile|desktop]
# Example: python clone_theme_from_website.py marsghc.com theme_abc12345 Home --viewport mobile
#
# This script orchestrates the theme cloning process:
# - Creates intermediate_files and theme_code directories inside theme-projects/<project_folder>
# - Uses the other scripts in sequence, passing --output-dir and --output-file as needed
# - Maps page_type to the correct template file
# - Returns the project folder name

import os
import sys
import subprocess
import re
import shutil
import time
import json

PAGE_TYPE_TO_TEMPLATE = {
    "home": "index.json",
    "collection": "collection.json",
    "product": "product.json",
    "allblogs": "blog.json",
    "singleblog": "article.json"
}

SCRIPTS = {
    "get_url": "get_shopify_page_url_from_sitemap.py",
    "screenshot": "take_shopify_screenshot.py",
    "design_doc": "generate_prompt_from_image.py",
    "section_plan": "generate_section_design_plan.py",
    "theme_examples": "generate_theme_examples.py",
    "shopify_section": "generate_shopify_section.py",
    "shopify_page": "generate_shopify_page_from_settings.py"
}

THEME_PROJECTS_DIR = "theme-projects"
INTERMEDIATE_DIR_NAME = "intermediate_files"
THEME_CODE_DIR_NAME = "theme_code"


def run_script(args, capture_output=False):
    result = subprocess.run(args, capture_output=capture_output, text=True)
    if result.returncode != 0:
        print(f"Error running: {' '.join(args)}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip() if capture_output else None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Clone a Shopify theme project from a website and page type.")
    parser.add_argument("website", help="Website domain (e.g., marsghc.com)")
    parser.add_argument("project_folder", help="Project folder name (e.g., theme_abc12345)")
    parser.add_argument("page_type", help="Page type (Home, Collection, Product, AllBlogs, SingleBlog)")
    parser.add_argument("--viewport", default="mobile", choices=["desktop", "mobile"], help="Viewport to use (desktop or mobile). Default: mobile")
    args = parser.parse_args()

    website = args.website
    project_folder = args.project_folder
    page_type = args.page_type.lower()
    viewport = args.viewport
    if page_type not in PAGE_TYPE_TO_TEMPLATE:
        print(f"Invalid page_type. Must be one of: {', '.join(PAGE_TYPE_TO_TEMPLATE.keys())}")
        sys.exit(1)

    # Set up directories
    project_path = os.path.join(THEME_PROJECTS_DIR, project_folder)
    intermediate_dir = os.path.join(project_path, INTERMEDIATE_DIR_NAME)
    theme_code_dir = os.path.join(project_path, THEME_CODE_DIR_NAME)

    # 1. Get the target page URL
    print(f"\n[Step 1] Resolving canonical URL using: {SCRIPTS['get_url']} {website} {page_type}")
    url = run_script([
        sys.executable, SCRIPTS["get_url"], website, page_type
    ], capture_output=True)
    url = url.split(": ")[-1] if ": " in url else url
    print(f"Target page URL: {url}")

    # Sanitize URL for filesystem use
    url_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', url)

    # Directory structure (url/viewport as parent)
    parent_dir = os.path.join(intermediate_dir, url_safe, viewport)
    screenshots_dir = os.path.join(parent_dir, "screenshots")
    design_docs_dir = os.path.join(parent_dir, "design_docs")
    section_plans_dir = os.path.join(parent_dir, "section_design_plans")
    examples_dir = os.path.join(parent_dir, "theme_examples")
    sections_dir = os.path.join(section_plans_dir, "sections")
    iteration_dir = os.path.join(parent_dir, "iterations")
    code_changes_sections = os.path.join(parent_dir, "code_changes", "sections")
    code_changes_templates = os.path.join(parent_dir, "code_changes", "templates")
    theme_code_parent = os.path.join(theme_code_dir, website, viewport)
    shopify_code_dir = os.path.join(theme_code_parent, "sections")
    templates_dir = os.path.join(theme_code_parent, "templates")
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(design_docs_dir, exist_ok=True)
    os.makedirs(section_plans_dir, exist_ok=True)
    os.makedirs(examples_dir, exist_ok=True)
    os.makedirs(sections_dir, exist_ok=True)
    os.makedirs(code_changes_sections, exist_ok=True)
    os.makedirs(code_changes_templates, exist_ok=True)
    os.makedirs(shopify_code_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)

    # Checkpoint file path
    checkpoint_path = os.path.join(parent_dir, "checkpoint.json")
    checkpoint = {}
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
    def save_checkpoint(step):
        checkpoint[step] = True
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)

    # 2. Take screenshots
    if not checkpoint.get("screenshots"):
        print(f"\n[Step 2] Taking screenshots using: {SCRIPTS['screenshot']} {website} {viewport} --output-dir {screenshots_dir}")
        run_script([
            sys.executable, SCRIPTS["screenshot"], website, viewport, "--output-dir", screenshots_dir
        ])
        save_checkpoint("screenshots")
    else:
        print("[Checkpoint] Skipping screenshots step.")

    # 3. Generate design documentation
    if not checkpoint.get("design_docs"):
        print(f"\n[Step 3] Generating design documentation using: {SCRIPTS['design_doc']} --input-dir {screenshots_dir} --output-dir {design_docs_dir}")
        run_script([
            sys.executable, SCRIPTS["design_doc"], "--input-dir", screenshots_dir, "--output-dir", design_docs_dir
        ])
        save_checkpoint("design_docs")
    else:
        print("[Checkpoint] Skipping design_docs step.")

    # 4. Generate section design plans (SKIPPED)
    # if not checkpoint.get("section_plans"):
    #     print(f"\n[Step 4] Generating section design plans using: {SCRIPTS['section_plan']} --design-docs-dir {design_docs_dir} --screenshots-dir {screenshots_dir} --output-dir {section_plans_dir}")
    #     run_script([
    #         sys.executable, SCRIPTS["section_plan"], "--design-docs-dir", design_docs_dir, "--screenshots-dir", screenshots_dir, "--output-dir", section_plans_dir
    #     ])
    #     save_checkpoint("section_plans")
    # else:
    #     print("[Checkpoint] Skipping section_plans step.")

    # 5. Generate theme examples (use design_docs_dir as sections_dir)
    if not checkpoint.get("theme_examples"):
        print(f"\n[Step 4] Generating theme examples using: {SCRIPTS['theme_examples']} --sections-dir {design_docs_dir} --output-dir {examples_dir}")
        run_script([
            sys.executable, SCRIPTS["theme_examples"], "--sections-dir", design_docs_dir, "--output-dir", examples_dir
        ])
        save_checkpoint("theme_examples")
    else:
        print("[Checkpoint] Skipping theme_examples step.")

    # 6. Generate Shopify sections (use design_docs_dir as sections_dir)
    if not checkpoint.get("shopify_sections"):
        print(f"\n[Step 5] Generating Shopify sections using: {SCRIPTS['shopify_section']} --sections-dir {design_docs_dir} --examples-dir {examples_dir} --output-dir {code_changes_sections}")
        run_script([
            sys.executable, SCRIPTS["shopify_section"], "--sections-dir", design_docs_dir, "--examples-dir", examples_dir, "--output-dir", code_changes_sections
        ])
        save_checkpoint("shopify_sections")
    else:
        print("[Checkpoint] Skipping shopify_sections step.")

    # 7. Generate the page template (use design_docs_dir as sections_dir)
    if not checkpoint.get("shopify_page"):
        template_file = PAGE_TYPE_TO_TEMPLATE[page_type]
        output_file = os.path.join(code_changes_templates, template_file)
        print(f"\n[Step 6] Generating Shopify page template using: {SCRIPTS['shopify_page']} --sections-dir {design_docs_dir} --shopify-code-dir {code_changes_sections} --output-dir {code_changes_templates} --output-file {output_file}")
        run_script([
            sys.executable, SCRIPTS["shopify_page"], "--shopify-code-dir", code_changes_sections, "--output-dir", code_changes_templates, "--output-file", output_file
        ])
        save_checkpoint("shopify_page")
    else:
        print("[Checkpoint] Skipping shopify_page step.")

    # 8. Copy code_changes to canonical theme_code (flat, not nested by website/viewport)
    if not checkpoint.get("code_copy"):
        print(f"\n[Step 7] Copying generated code to canonical theme_code directory")
        def copy_sections_with_epoch(src, dst, epoch):
            if not os.path.exists(src):
                return {}
            mapping = {}
            for item in os.listdir(src):
                s = os.path.join(src, item)
                if os.path.isfile(s) and s.endswith('.liquid'):
                    base, ext = os.path.splitext(item)
                    new_name = f"{base}-{epoch}{ext}"
                    # If new_name is more than 50 characters, shorten base from behind
                    if len(new_name) > 50:
                        # Calculate how many characters base can be
                        allowed_base_len = 49 - len(ext) - len(epoch) - 1  # 1 for dash
                        base_new = base[:allowed_base_len]
                        new_name = f"{base_new}-{epoch}{ext}"
                    d = os.path.join(dst, new_name)
                    os.makedirs(dst, exist_ok=True)
                    shutil.copy2(s, d)
                    mapping[base] = new_name.replace('.liquid', '')
            return mapping

        def copy_template_with_section_types(src, dst, section_type_map):
            if not os.path.exists(src):
                return
            for item in os.listdir(src):
                s = os.path.join(src, item)
                if os.path.isfile(s) and item.endswith('.json'):
                    with open(s, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Update section type fields
                    if 'sections' in data:
                        for section_key, section_val in data['sections'].items():
                            orig_type = section_val.get('type')
                            if orig_type and orig_type in section_type_map:
                                section_val['type'] = section_type_map[orig_type]
                    d = os.path.join(dst, item)
                    os.makedirs(dst, exist_ok=True)
                    with open(d, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)

        # Copy sections with epoch suffix and build mapping
        epoch = str(int(time.time()))
        section_type_map = copy_sections_with_epoch(code_changes_sections, os.path.join(theme_code_dir, "sections"), epoch)
        copy_sections_with_epoch(code_changes_sections, os.path.join(iteration_dir, "original", "sections"), epoch)
        # Copy templates, updating section type fields
        copy_template_with_section_types(code_changes_templates, os.path.join(theme_code_dir, "templates"), section_type_map)
        copy_template_with_section_types(code_changes_templates, os.path.join(iteration_dir, "original", "templates"), section_type_map)
        save_checkpoint("code_copy")
    else:
        print("[Checkpoint] Skipping code_copy step.")

    print(f"\nTheme project created: {project_folder}")
    print(f"Theme code: {theme_code_dir}")
    print(f"Intermediate files: {intermediate_dir}")
    print(f"Main template: {output_file}")
    print(project_folder)

if __name__ == "__main__":
    main() 