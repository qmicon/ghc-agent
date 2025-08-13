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
from dotenv import load_dotenv
load_dotenv()

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

def truncate_content(content: str, max_lines: int = 150) -> str:
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

def extract_code_examples(workspace_dir: str, primary_keywords: set, secondary_keywords: set, max_examples: int = 10) -> list:
    """Extract code examples from workspace directories based on keywords."""
    examples = []
    
    # Search through sections
    sections_dir = os.path.join(workspace_dir, "sections")
    if os.path.exists(sections_dir):
        for file in os.listdir(sections_dir):
            if file.endswith(".liquid"):
                file_path = os.path.join(sections_dir, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        score = calculate_relevance_score(content, primary_keywords, secondary_keywords)
                        if score > 0:
                            referenced_files, referenced_assets = find_referenced_files(content, workspace_dir, primary_keywords, secondary_keywords)
                            examples.append({
                                "type": "section",
                                "handle": file.replace(".liquid", ""),
                                "content": truncate_content(content),
                                "score": score,
                                "referenced_files": referenced_files,
                                "referenced_assets": referenced_assets
                            })
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    
    # Search through snippets
    snippets_dir = os.path.join(workspace_dir, "snippets")
    if os.path.exists(snippets_dir):
        for file in os.listdir(snippets_dir):
            if file.endswith(".liquid"):
                file_path = os.path.join(snippets_dir, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        score = calculate_relevance_score(content, primary_keywords, secondary_keywords)
                        if score > 0:
                            referenced_files, referenced_assets = find_referenced_files(content, workspace_dir, primary_keywords, secondary_keywords)
                            examples.append({
                                "type": "snippet",
                                "handle": file.replace(".liquid", ""),
                                "content": truncate_content(content),
                                "score": score,
                                "referenced_files": referenced_files,
                                "referenced_assets": referenced_assets
                            })
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    
    # Sort by score and limit number of examples
    examples.sort(key=lambda x: x["score"], reverse=True)
    return examples[:max_examples]

def format_example(examples: list) -> str:
    """Format code examples for the prompt, ensuring unique files."""
    output = []
    seen_files = set()  # Track files we've already processed
    
    # Process main examples first
    for example in examples:
        content_hash = hash(example['content'])
        if content_hash not in seen_files:
            seen_files.add(content_hash)
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
    
    # Process referenced files
    referenced_output = []
    for example in examples:
        if example["referenced_files"]:
            for ref in example["referenced_files"]:
                content_hash = hash(ref['content'])
                if content_hash not in seen_files:
                    seen_files.add(content_hash)
                    referenced_output.append(f"""
Referenced {ref['type'].title()}: {ref['handle']}
```liquid
{ref['content']}
```
""")
    
    # Add referenced files section if we have any
    if referenced_output:
        output.append("\nReferenced Files:")
        output.extend(referenced_output)
    
    # Process referenced assets
    asset_output = []
    seen_assets = set()
    for example in examples:
        if example["referenced_assets"]:
            for asset in example["referenced_assets"]:
                asset_path = asset.get('path', '')
                if asset_path and asset_path not in seen_assets:
                    seen_assets.add(asset_path)
                    asset_output.append(f"- {asset['path']} ({asset['extension']})")
    
    # Add referenced assets section if we have any
    if asset_output:
        output.append("\nReferenced Assets:")
        output.extend(asset_output)
    
    return "\n".join(output)

def extract_code_examples_from_dataset(dataset_dir: str) -> list:
    """Extract code examples from dataset directory and format them as implementation examples."""
    examples = []
    
    if not os.path.exists(dataset_dir):
        print(f"Warning: {dataset_dir} not found")
        return examples
    
    # Walk through the dataset directory
    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            if file.endswith(('.liquid', '.json')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        # Determine file type and path
                        if file.endswith('.json'):
                            file_type = 'json'
                            relative_path = os.path.join('templates', file)
                        else:
                            file_type = 'liquid'
                            if 'sections' in root:
                                relative_path = os.path.join('sections', file)
                            else:
                                relative_path = os.path.join('snippets', file)
                        
                        examples.append({
                            "type": "implementation",
                            "file_path": relative_path,
                            "file_type": file_type,
                            "content": truncate_content(content, 500)
                        })
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    
    return examples

def format_implementation_example(example: dict) -> str:
    """Format an implementation example for the prompt."""
    return f"""
---
FILE: {example['file_path']}
TYPE: {example['file_type']}
CONTENT:
```{example['file_type']}
{example['content']}
```
---"""

async def get_dataset_purposes() -> dict:
    """Read purposes from prompt.txt files in dataset directories."""
    purposes = {}
    dataset_dir = "dataset"
    
    if not os.path.exists(dataset_dir):
        print(f"Warning: {dataset_dir} not found")
        return purposes
    
    for dir_name in os.listdir(dataset_dir):
        prompt_path = os.path.join(dataset_dir, dir_name, "prompt.txt")
        if os.path.exists(prompt_path):
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    # Get first line as purpose
                    purpose = f.readline().strip()
                    purposes[dir_name] = purpose
            except Exception as e:
                print(f"Warning: Could not read {prompt_path}: {e}")
    
    return purposes

async def find_most_relevant_dataset(requirements: str) -> str:
    """Find the most relevant dataset directory based on requirements."""
    # Get purposes from prompt.txt files
    dataset_purposes = await get_dataset_purposes()
    
    # Format purposes for prompt
    purposes_text = "\n".join([f"{dir_name}: {purpose}" for dir_name, purpose in dataset_purposes.items()])
    
    prompt = f"""
    Given these offer page requirements:
    ---
    {requirements}
    ---

    And these dataset directories with their purposes:
    ---
    {purposes_text}
    ---

    Return ONLY the name of the most relevant dataset directory that best matches the requirements, no other text.
    Return format should be just the directory name, nothing else.
    """
    
    resp = await keyword_llm.ainvoke([HumanMessage(content=prompt)])
    return resp.content.strip()

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
    
    # Find most relevant dataset directory
    print("\nFinding most relevant dataset directory...")
    relevant_dataset = await find_most_relevant_dataset(requirements)
    print(f"Selected dataset: {relevant_dataset}")
    
    # Extract UI component examples from workspace
    print("\nSearching for relevant UI component examples...")
    ui_examples = extract_code_examples("example_components", primary_keywords, secondary_keywords, max_examples=20)
    
    # Extract implementation examples from selected dataset
    print(f"\nExtracting implementation examples from {relevant_dataset}...")
    implementation_examples = extract_code_examples_from_dataset(f"dataset/{relevant_dataset}")
    
    if not ui_examples and not implementation_examples:
        print("❌ No relevant examples found")
        return
    
    # Format and save examples
    with open("examples.txt", "w", encoding="utf-8") as f:
        # Write implementation examples
        if implementation_examples:
            f.write("OFFER PAGE IMPLEMENTATION CODE EXAMPLES\n")
            f.write("=" * 50 + "\n\n")
            formatted_impl_examples = [format_implementation_example(ex) for ex in implementation_examples]
            f.write("\n".join(formatted_impl_examples))

        # Write UI component examples
        if ui_examples:
            if implementation_examples:
                f.write("\n\n")  # Add spacing between sections
            f.write("\n\nRELEVANT CODE EXAMPLES FOR UI COMPONENTS\n")
            f.write("=" * 50 + "\n\n")
            formatted_ui_examples = format_example(ui_examples)
            f.write(formatted_ui_examples)
    
    print("✓ Examples saved to examples.txt")

if __name__ == "__main__":
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")
    
    asyncio.run(generate_examples()) 