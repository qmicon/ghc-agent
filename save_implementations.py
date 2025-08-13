#!/usr/bin/env python3
"""
save_implementations.py
-----------------------------------------------------------------
INPUTS
  offer_plan.txt              # Generated plan with code blocks
  workspace/                  # Directory to save implementations

OUTPUT
  workspace/                  # Files created based on code blocks
"""

import os
import re
from pathlib import Path
import argparse

def extract_code_blocks(plan_content: str) -> list:
    """Extract code blocks from the plan content."""
    # Pattern to match code blocks between --- markers
    pattern = r"FILE: (.*?)\nTYPE: (.*?)\nCONTENT:\s*\n```(.*?)\n(.*?)```\s*\n"
    
    # Find all matches
    matches = re.finditer(pattern, plan_content, re.DOTALL)
    
    # Extract file info and content
    code_blocks = []
    for match in matches:
        file_path = match.group(1).strip()
        file_type = match.group(2).strip()
        content_type = match.group(3).strip()
        content = match.group(4).strip()
        
        code_blocks.append({
            'file_path': file_path,
            'file_type': file_type,
            'content_type': content_type,
            'content': content
        })
    
    return code_blocks

def save_code_blocks(code_blocks: list, base_dir: str = "claude_workspace"):
    """Save code blocks to their respective files."""
    for block in code_blocks:
        # Create full path
        full_path = os.path.join(base_dir, block['file_path'])
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Save file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(block['content'])
        print(f"✓ Saved: {block['file_path']}")

def main():
    parser = argparse.ArgumentParser(description="Save implementation files from either the main plan or the converted one-file plan.")
    parser.add_argument(
        "--source",
        choices=["main", "converted"],
        default="converted",
        help="Select the source plan to read code blocks from: 'main' uses offer_plan_claude.txt, 'converted' uses one_page_offer_from_plan.txt (default)."
    )
    args = parser.parse_args()

    plan_file = "offer_plan_claude.txt" if args.source == "main" else "one_page_offer_from_plan.txt"

    # Read the plan file
    try:
        with open(plan_file, "r", encoding="utf-8") as f:
            plan_content = f.read()
    except FileNotFoundError:
        print(f"❌ {plan_file} not found")
        return
    except Exception as e:
        print(f"❌ Error reading {plan_file}: {e}")
        return
    
    # Extract code blocks
    print("Extracting code blocks from plan...")
    code_blocks = extract_code_blocks(plan_content)
    
    if not code_blocks:
        print("❌ No code blocks found in plan")
        return
    
    # Save code blocks
    print(f"\nFound {len(code_blocks)} code blocks to save:")
    for block in code_blocks:
        print(f"- {block['file_path']} ({block['file_type']})")
    
    print("\nSaving files...")
    save_code_blocks(code_blocks)
    print("\n✓ All files saved successfully")

if __name__ == "__main__":
    main() 