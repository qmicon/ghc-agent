#!/usr/bin/env python3
"""
apply_edits.py
-----------------------------------------------------------------
Applies suggested edits to files by:
1. Reading suggested_edits.txt
2. Parsing SEARCH/REPLACE blocks
3. Creating edited files in claude_workspace_edits directory
"""

import os
import re
import shutil
from pathlib import Path

def parse_edits(edits_file: str = "suggested_edits.txt") -> list:
    """Parse suggested edits file into a list of edit operations."""
    try:
        with open(edits_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ {edits_file} not found")
        return []
    except Exception as e:
        print(f"❌ Error reading {edits_file}: {e}")
        return []

    # Find all SEARCH/REPLACE blocks with their line numbers
    # This regex looks for the pattern:
    # <<<<<<< SEARCH
    # [content]
    # =======
    # [content]
    # >>>>>>> REPLACE
    search_replace_pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
    matches = list(re.finditer(search_replace_pattern, content, re.DOTALL))
    
    edits = []
    for match in matches:
        # Get the line number where this block starts
        start_line = content[:match.start()].count('\n') + 1
        
        # Get the file path from the line above the block
        # Look for the last non-empty line before the block
        lines_before = content[:match.start()].split('\n')
        file_path = None
        for line in reversed(lines_before):
            line = line.strip()
            if line and not line.startswith(('#', '##', '```')):
                file_path = line.replace('\\', '/')  # Normalize path separators
                break
        
        if not file_path:
            print(f"❌ Could not find file path for edit at line {start_line}")
            continue
        
        # Get the search and replace content
        search_content = match.group(1)
        replace_content = match.group(2)
        
        # Get the edit description (header above the file path)
        description = None
        for line in reversed(lines_before):
            if line.startswith('## '):
                description = line.strip()
                break
        
        edits.append({
            'file': file_path,
            'search': search_content,
            'replace': replace_content,
            'description': description or f"Edit at line {start_line}"
        })
    
    return edits

def ensure_edits_directory(workspace_dir: str) -> str:
    """Create and return path to edits directory."""
    edits_dir = os.path.join(os.path.dirname(workspace_dir), "claude_workspace_edits")
    if os.path.exists(edits_dir):
        # Clear existing edits directory
        shutil.rmtree(edits_dir)
    # Create fresh edits directory
    os.makedirs(edits_dir)
    return edits_dir

def copy_workspace_to_edits(workspace_dir: str, edits_dir: str):
    """Copy all files from workspace to edits directory."""
    for root, dirs, files in os.walk(workspace_dir):
        # Calculate relative path from workspace_dir
        rel_path = os.path.relpath(root, workspace_dir)
        # Create corresponding directory in edits_dir
        target_dir = os.path.join(edits_dir, rel_path)
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy all files
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_dir, file)
            shutil.copy2(src_file, dst_file)

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text by:
    1. Converting all whitespace sequences to single spaces
    2. Stripping leading/trailing whitespace
    3. Normalizing line endings
    """
    # First normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Then normalize all whitespace sequences
    lines = [line.strip() for line in text.split('\n')]
    # Remove empty lines and join with single newline
    return '\n'.join(line for line in lines if line)

def apply_edit(workspace_dir: str, edits_dir: str, edit: dict) -> bool:
    """Apply a single edit to a file in the edits directory."""
    # Get paths for both original and edited files
    original_file = os.path.join(workspace_dir, edit['file'])
    edited_file = os.path.join(edits_dir, edit['file'])
    
    try:
        # Read current file content
        with open(original_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Normalize whitespace in both search content and file content
        normalized_search = normalize_whitespace(edit['search'])
        normalized_content = normalize_whitespace(content)
        
        # Check if search content exists in file
        if normalized_search not in normalized_content:
            print(f"❌ Search content not found in {edit['file']}")
            print(f"Edit: {edit['description']}")
            print("Expected content (normalized):")
            print(normalized_search)
            print("\nFirst 100 chars of file content (normalized):")
            print(normalized_content[:100])
            return False
        
        # Find the actual search content in the original file
        search_pos = normalized_content.find(normalized_search)
        if search_pos == -1:
            print(f"❌ Could not map normalized search back to original content in {edit['file']}")
            return False
            
        # Count newlines up to search_pos in normalized content to find line number
        line_num = normalized_content[:search_pos].count('\n') + 1
        print(f"Found search content at line {line_num}")
        
        # Apply the edit using the original content
        new_content = content.replace(edit['search'], edit['replace'], 1)  # Replace only first occurrence
        
        # Ensure the target directory exists
        os.makedirs(os.path.dirname(edited_file), exist_ok=True)
        
        # Write updated content to the edits directory
        with open(edited_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print(f"✓ Created edited file at {edited_file}")
        print(f"Description: {edit['description']}")
        return True
        
    except FileNotFoundError:
        print(f"❌ File not found: {edit['file']}")
        print(f"Edit: {edit['description']}")
        return False
    except Exception as e:
        print(f"❌ Error applying edit to {edit['file']}: {e}")
        print(f"Edit: {edit['description']}")
        return False

def main():
    workspace_dir = "claude_workspace"
    
    # Create and prepare edits directory
    print("Preparing edits directory...")
    edits_dir = ensure_edits_directory(workspace_dir)
    copy_workspace_to_edits(workspace_dir, edits_dir)
    print(f"Created fresh edits directory at {edits_dir}")
    
    # Parse edits
    print("\nReading suggested edits...")
    edits = parse_edits()
    if not edits:
        print("❌ No edits found to apply")
        return
    
    print(f"Found {len(edits)} edits to apply")
    
    # Apply each edit
    success_count = 0
    for i, edit in enumerate(edits, 1):
        print(f"\nApplying edit {i}/{len(edits)}...")
        if apply_edit(workspace_dir, edits_dir, edit):
            success_count += 1
    
    # Print summary
    print(f"\nEdit Summary:")
    print(f"Total edits: {len(edits)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(edits) - success_count}")
    print(f"\nEdited files are available in: {edits_dir}")

if __name__ == "__main__":
    main() 