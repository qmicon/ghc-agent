#!/usr/bin/env python3
"""
generate_examples.py
-----------------------------------------------------------------
Generates code examples for the offer plan prompt by:
1. Generating relevant keywords
2. Searching through snippets and sections
3. Creating examples.txt with few-shot examples
"""

import os
import asyncio
import re
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

# Initialize LLM for keyword generation
keyword_llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0.0,
    max_tokens=100
)

async def generate_relevant_keywords(requirements: str) -> tuple[set, set]:
    """Generate relevant keywords from user requirements using LLM."""
    prompt = f"""
    Given these offer page requirements:
    ---
    {requirements}
    ---

    Generate two lists of keywords:
    1. Primary keywords (most important for functionality)
    2. Secondary keywords (helpful but not critical)

    Focus on:
    1. UI components (e.g., timer, grid, button)
    2. Functionality (e.g., countdown, selector, cart)
    3. Data types (e.g., product, price, collection)
    4. Layout elements (e.g., horizontal, vertical, grid)

    Return in format:
    PRIMARY: keyword1, keyword2, ...
    SECONDARY: keyword1, keyword2, ...

    keywords should be one worded each
    """
    
    resp = await keyword_llm.ainvoke([HumanMessage(content=prompt)])
    content = resp.content
    
    # Extract primary and secondary keywords
    primary_match = re.search(r'PRIMARY:\s*(.*?)(?:\n|$)', content, re.DOTALL)
    secondary_match = re.search(r'SECONDARY:\s*(.*?)(?:\n|$)', content, re.DOTALL)
    
    primary_keywords = {k.strip().lower() for k in primary_match.group(1).split(",")} if primary_match else set()
    secondary_keywords = {k.strip().lower() for k in secondary_match.group(1).split(",")} if secondary_match else set()
    
    return primary_keywords, secondary_keywords

def calculate_relevance_score(content: str, primary_keywords: set, secondary_keywords: set) -> float:
    """Calculate relevance score for content based on keyword matches."""
    content_lower = content.lower()
    
    # Count primary keyword matches (weighted higher)
    primary_matches = sum(2 for keyword in primary_keywords if keyword in content_lower)
    
    # Count secondary keyword matches
    secondary_matches = sum(1 for keyword in secondary_keywords if keyword in content_lower)
    
    # Calculate total score
    total_score = primary_matches + secondary_matches
    
    # Normalize by content length to avoid bias towards longer files
    content_length = len(content.split())
    if content_length > 0:
        total_score = total_score / (content_length ** 0.5)  # Square root to reduce impact of length
    
    return total_score

def truncate_content(content: str, max_lines: int = 500) -> str:
    """Truncate content to a maximum number of lines, keeping important parts."""
    lines = content.split('\n')
    if len(lines) <= max_lines:
        return content
    
    # Keep first and last parts
    first_part = lines[:max_lines//2]
    last_part = lines[-max_lines//2:]
    
    return '\n'.join(first_part + ['... (truncated) ...'] + last_part)

def find_referenced_files(content: str, workspace_dir: str, primary_keywords: set, secondary_keywords: set) -> tuple[list, list]:
    """Find files referenced in the content (e.g., through render tags and assets)."""
    referenced_files = []
    referenced_assets = []
    
    # Find render tags
    render_pattern = r'{%\s*render\s+[\'"]([^\'"]+)[\'"]'
    render_matches = re.finditer(render_pattern, content)
    
    for match in render_matches:
        file_name = match.group(1)
        if not file_name.endswith('.liquid'):
            file_name += '.liquid'
        
        # Check in snippets directory
        snippet_path = os.path.join(workspace_dir, 'snippets', file_name)
        if os.path.exists(snippet_path):
            try:
                with open(snippet_path, 'r', encoding='utf-8') as f:
                    snippet_content = f.read()
                    # Calculate relevance score for the snippet
                    score = calculate_relevance_score(snippet_content, primary_keywords, secondary_keywords)
                    # Only include if it's relevant
                    if score > 0:
                        referenced_files.append({
                            'type': 'snippet',
                            'handle': file_name.replace('.liquid', ''),
                            'content': truncate_content(snippet_content),
                            'score': score
                        })
            except Exception as e:
                print(f"Warning: Could not read referenced file {snippet_path}: {e}")
    
    # Find asset references
    asset_patterns = [
        r'<link[^>]+href=[\'"]([^\'"]+\.(?:css|js))[\'"]',  # CSS and JS files
        r'<script[^>]+src=[\'"]([^\'"]+\.js)[\'"]',         # JS files
        r'{{[^}]*[\'"]([^\'"]+\.(?:css|js))[\'"][^}]*}}',   # Liquid asset_url filters
        r'{{[^}]*[\'"]([^\'"]+\.(?:css|js))[\'"][^}]*\|[^}]*asset_url[^}]*}}'  # Explicit asset_url filters
    ]
    
    for pattern in asset_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            asset_path = match.group(1)
            # Handle both relative and absolute paths
            if asset_path.startswith('/'):
                asset_path = asset_path[1:]  # Remove leading slash
            full_path = os.path.join(workspace_dir, 'assets', asset_path)
            
            if os.path.exists(full_path):
                referenced_assets.append({
                    'type': 'asset',
                    'path': asset_path,
                    'extension': os.path.splitext(asset_path)[1][1:].lower()
                })
    
    # Sort by relevance score
    referenced_files.sort(key=lambda x: x['score'], reverse=True)
    return referenced_files, referenced_assets

def extract_code_examples(dataset_dir: str, primary_keywords: set, secondary_keywords: set, max_examples: int = 10) -> list:
    """Extract code examples from dataset directories based on keywords."""
    examples = []
    seen_files = set()  # Track files we've already processed
    
    # Check if dataset directory exists
    if not os.path.exists(dataset_dir):
        print(f"Warning: {dataset_dir} not found")
        return examples
    
    # Search through all files in the directory
    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            if file.endswith((".liquid", ".js", ".css", ".json")):
                file_path = os.path.join(root, file)
                
            # Skip if we've already processed this file
            if file_path in seen_files:
                continue
            seen_files.add(file_path)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    score = calculate_relevance_score(content, primary_keywords, secondary_keywords)
                    if score > 0:
                        referenced_files, referenced_assets = find_referenced_files(content, dataset_dir, primary_keywords, secondary_keywords)
                        
                        # Filter out duplicate referenced files
                        unique_referenced_files = []
                        seen_refs = set()
                        for ref in referenced_files:
                            ref_path = ref.get('path', '')
                            if ref_path and ref_path not in seen_refs:
                                seen_refs.add(ref_path)
                                unique_referenced_files.append(ref)
                        
                        # Filter out duplicate assets
                        unique_assets = []
                        seen_assets = set()
                        for asset in referenced_assets:
                            asset_path = asset.get('path', '')
                            if asset_path and asset_path not in seen_assets:
                                seen_assets.add(asset_path)
                                unique_assets.append(asset)
                        
                        examples.append({
                            "type": "template" if file.endswith(('.liquid', '.json')) else "asset",
                            "handle": file,
                            "content": truncate_content(content),
                            "score": score,
                            "referenced_files": unique_referenced_files,
                            "referenced_assets": unique_assets
                        })
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
    
    # Sort by score and limit number of examples
    examples.sort(key=lambda x: x["score"], reverse=True)
    return examples[:max_examples]

def format_example(example: dict) -> str:
    """Format a code example for the prompt."""
    output = []
    
    # Main example
    if example["type"] == "section":
        output.append(f"""
Example Section: {example['handle']}
```liquid
{example['content']}
```
""")
    else:
        output.append(f"""
Example Snippet: {example['handle']}
```liquid
{example['content']}
```
""")
    
    # Referenced files
    if example["referenced_files"]:
        output.append("\nReferenced Files:")
        for ref in example["referenced_files"]:
            output.append(f"""
Referenced {ref['type'].title()}: {ref['handle']}
```liquid
{ref['content']}
```
""")
    
    # Referenced assets
    if example["referenced_assets"]:
        output.append("\nReferenced Assets:")
        for asset in example["referenced_assets"]:
            output.append(f"- {asset['path']} ({asset['extension']})")
    
    return "\n".join(output)

async def generate_examples():
    # Read requirements from file
    try:
        with open("offer_requirements_prompt.txt", "r", encoding="utf-8") as f:
            requirements = f.read()
    except FileNotFoundError:
        print("❌ offer_requirements_prompt.txt not found")
        return
    except Exception as e:
        print(f"❌ Error reading offer_requirements_prompt.txt: {e}")
        return
    
    # Generate keywords
    print("Generating keywords...")
    primary_keywords, secondary_keywords = await generate_relevant_keywords(requirements)
    print(f"Primary keywords: {', '.join(primary_keywords)}")
    print(f"Secondary keywords: {', '.join(secondary_keywords)}")
    
    # Define directories to search in dataset
    dataset_dirs = [
        "dataset/desc-buy-x-for-y",
        "dataset/simple-buy-x-for-y"
    ]
    
    all_examples = []
    seen_examples = set()  # Track examples we've already processed
    
    # Extract examples from each directory
    print("\nSearching for relevant examples...")
    for dir_path in dataset_dirs:
        print(f"\nSearching in {dir_path}...")
        examples = extract_code_examples(dir_path, primary_keywords, secondary_keywords, max_examples=8)
        if examples:
            # Filter out duplicate examples based on content
            for example in examples:
                content_hash = hash(example['content'])
                if content_hash not in seen_examples:
                    seen_examples.add(content_hash)
                    all_examples.append(example)
            print(f"Found {len(examples)} relevant examples")
    
    if not all_examples:
        print("❌ No relevant examples found")
        return
    
    # Format and save examples
    print(f"\nFound {len(all_examples)} most relevant examples")
    formatted_examples = [format_example(ex) for ex in all_examples]
    
    # Save to file
    with open("examples.txt", "w", encoding="utf-8") as f:
        f.write("RELEVANT CODE EXAMPLES\n")
        f.write("=" * 50 + "\n\n")
        f.write("\n".join(formatted_examples))
    
    print("✓ Examples saved to examples.txt")

if __name__ == "__main__":
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")
    
    asyncio.run(generate_examples()) 