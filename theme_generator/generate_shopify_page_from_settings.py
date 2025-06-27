#!/usr/bin/env python3
"""
generate_shopify_page_from_settings.py
-------------------------------------------------------------
Generates a Shopify page template JSON using section settings JSON files and corresponding .liquid files.
Section order is determined by the section number in the settings_*.json filenames.
"""
import os
import json
import argparse
glob_imported = False
try:
    import glob
    glob_imported = True
except ImportError:
    pass

def get_section_order_and_settings(sections_dir):
    """Return a list of (section_number, section_type, type_value, section_settings) sorted by section_number."""
    section_files = []
    for file in os.listdir(sections_dir):
        if file.startswith("settings_") and file.endswith(".json"):
            try:
                # Extract section number from filename
                base = file[len("settings_"):-len(".json")]
                section_number = int(base.split("-")[0])
                with open(os.path.join(sections_dir, file), "r", encoding="utf-8") as f:
                    settings_json = json.load(f)
                # The first (and only) key in the settings file is the section type
                if not settings_json:
                    raise ValueError(f"Empty settings file: {file}")
                section_type = list(settings_json.keys())[0]
                section_obj = settings_json[section_type]
                type_value = section_obj.get("type", section_type)
                section_settings = section_obj.get("settings", {})
                section_files.append((section_number, section_type, type_value, section_settings))
            except Exception as e:
                print(f"Warning: Could not parse {file}: {e}")
    section_files.sort(key=lambda x: x[0])
    return section_files

def generate_page_template(sections):
    """Generate the Shopify page template JSON structure."""
    template = {
        "sections": {},
        "order": []
    }
    for idx, (section_number, section_type, type_value, section_settings) in enumerate(sections, 1):
        section_id = f"{section_type}_{idx}"
        template["sections"][section_id] = {
            "type": type_value,
            "settings": section_settings
        }
        template["order"].append(section_id)
    return template

def main():
    parser = argparse.ArgumentParser(description="Generate Shopify page template from section settings JSON files.")
    parser.add_argument("--shopify-code-dir", required=True, help="Directory containing settings_*.json and .liquid section files")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated page template")
    parser.add_argument("--output-file", required=True, help="Output file path for the main page JSON (e.g., index.json)")
    args = parser.parse_args()

    if not os.path.exists(args.shopify_code_dir):
        raise FileNotFoundError(f"Shopify code dir not found: {args.shopify_code_dir}")
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[INFO] Reading section settings from: {args.shopify_code_dir}")
    sections = get_section_order_and_settings(args.shopify_code_dir)
    if not sections:
        raise ValueError("No settings_*.json files found in sections dir.")
    print(f"[INFO] Found {len(sections)} sections.")

    print(f"[INFO] Generating Shopify page template JSON...")
    template = generate_page_template(sections)

    output_path = args.output_file
    if not os.path.isabs(output_path):
        output_path = os.path.join(args.output_dir, output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    print(f"[INFO] Shopify page template saved to: {output_path}")

if __name__ == "__main__":
    main() 