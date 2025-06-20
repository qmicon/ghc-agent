#!/usr/bin/env python3
"""
generate_theme_examples.py
-----------------------------------------------------------------
Generates code examples for theme generation by:
1. Analyzing design docs and dataset purposes
2. Selecting relevant datasets and generating keywords
3. Creating examples.txt with implementation examples
"""

import os
import asyncio
import re
import json
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import glob

load_dotenv()

# Initialize LLM for dataset selection and keyword generation
analysis_llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.0,
    max_tokens=10000
).with_retry(
    stop_after_attempt=5,  # Maximum number of attempts
    wait_exponential_jitter=True,  # Add jitter to the exponential backoff
    retry_if_exception_type=(Exception,),  # Retry on any exception
    exponential_jitter_params={
        "initial": 5,  # Initial delay in seconds
        "max": 60,  # Maximum delay in seconds
        "exp_base": 2,  # Base for exponential backoff
        "jitter": 0.1  # Random jitter factor
    }
)

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

def get_section_number(section_file: str) -> int:
    """Extract section number from filename (e.g., '01-hero-section.md' -> 1)."""
    match = re.match(r'^(\d+)-', os.path.basename(section_file))
    if not match:
        raise ValueError(f"Invalid section filename format: {section_file}. Must start with a number followed by a hyphen.")
    return int(match.group(1))

def get_all_section_files(sections_dir: str) -> list:
    """Get all section files from the sections directory."""
    if not os.path.exists(sections_dir):
        raise FileNotFoundError(f"Sections directory not found: {sections_dir}")
    section_files = []
    for file in glob.glob(os.path.join(sections_dir, "*.md")):
        try:
            section_number = get_section_number(file)
            section_files.append((section_number, os.path.basename(file)))
        except ValueError as e:
            print(f"Warning: {e}")
    section_files.sort(key=lambda x: x[0])
    return section_files

def get_design_docs(sections_dir: str, section_number: int = None) -> str:
    """Get design documentation for a specific section or all sections in the directory."""
    design_docs = []
    if section_number is not None:
        pattern = f"{section_number:02d}-*.md"
        matching_files = glob.glob(os.path.join(sections_dir, pattern))
        if not matching_files:
            raise FileNotFoundError(f"No section file found starting with {section_number}- in {sections_dir}")
        section_file = matching_files[0]
        with open(section_file, "r", encoding="utf-8") as f:
            design_docs.append({
                "filename": os.path.basename(section_file),
                "content": f.read()
            })
    else:
        md_files = sorted(Path(sections_dir).glob("*.md"))
        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                design_docs.append({
                    "filename": md_file.name,
                    "content": f.read()
                })
    return "\n\n".join([f"## {doc['filename']}\n{doc['content']}" for doc in design_docs])

async def analyze_design_and_select_datasets(design_docs: str, dataset_purposes: dict) -> dict:
    """Analyze design docs and select relevant datasets with keywords in a single LLM call."""
    system_prompt = """
    You are a Shopify theme expert tasked with analyzing design documentation and selecting relevant implementation examples.
    
    Your task is to:
    1. First create a detailed analysis plan
    2. Then generate a structured JSON response
    
    Analysis Plan should include:
    1. Key design elements and patterns identified
    2. Required functionality and components
    3. Technical requirements and constraints
    4. Selection criteria for datasets
    5. Keyword generation strategy
    
    After the plan, generate a JSON response that includes:
    1. Selected datasets with relevance scores
    2. Primary and secondary keywords for each dataset
    3. Reasoning for each selection
    4. Keyword should be only one word
    5. These keywords will be used to search relevant files in the shopify theme dataset
    
    Focus on:
    - UI components and patterns
    - Layout structures
    - Interactive elements
    - Design styles and themes
    - Technical implementations
    - Shopify-specific features
    
    json response format must be:
    ```json
    {
        "datasets": [
            {
                "name": "dataset-directory-name",
                "relevance_score": 0.95,
                "reasoning": "explanation of why this dataset is relevant",
                "primary_keywords": ["keyword1", "keyword2", ...],
                "secondary_keywords": ["keyword1", "keyword2", ...]
            },
            ...
        ]
    }
    ```
    """
    
    # Format dataset purposes for the prompt
    purposes_text = "\n".join([f"{dir_name}: {purpose}" for dir_name, purpose in dataset_purposes.items()])
    
    user_prompt = f"""
    Analyze the following design documentation and dataset purposes to select relevant implementation examples.

    Design Documentation:
    ---
    {design_docs}
    ---

    Available Datasets:
    ---
    {purposes_text}
    ---

    Please analyze the design documentation and:
    1. Create a detailed analysis plan
    2. Select the most relevant datasets
    3. Generate appropriate keywords for each dataset
    4. Provide reasoning for each selection
    
    Return the analysis and selections in the specified JSON format.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    try:
        # Get analysis from Claude
        response = await analysis_llm.ainvoke(messages)
        content = response.content.strip()
        
        # Save raw response content
        raw_response_file = os.path.join("screenshots", "raw_analysis.txt")
        os.makedirs(os.path.dirname(raw_response_file), exist_ok=True)
        with open(raw_response_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n✓ Raw analysis saved to {raw_response_file}")
        
        # Extract JSON from response
        json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response")
        
        # Parse JSON
        analysis_data = json.loads(json_match.group(1))
        
        # Validate required fields
        required_fields = ["datasets"]
        for field in required_fields:
            if field not in analysis_data:
                raise ValueError(f"Missing required field: {field}")
        
        for dataset in analysis_data["datasets"]:
            dataset_fields = ["name", "relevance_score", "reasoning", "primary_keywords", "secondary_keywords"]
            for field in dataset_fields:
                if field not in dataset:
                    raise ValueError(f"Missing required field in dataset: {field}")
        
        return analysis_data
        
    except Exception as e:
        print(f"Error analyzing design and selecting datasets: {str(e)}")
        return None

def truncate_content(content: str, max_lines: int = 150) -> str:
    """Truncate content to a maximum number of lines, keeping important parts."""
    lines = content.split('\n')
    if len(lines) <= max_lines:
        return content
    # Keep first and last parts
    first_part = lines[:max_lines//2]
    last_part = lines[-max_lines//2:]
    return '\n'.join(first_part + ['... (truncated) ...'] + last_part)

def extract_code_examples_from_dataset(dataset_dir: str, keywords: dict, max_lines: int = 150) -> list:
    """Extract code examples from dataset directory based on keywords. Only .liquid files, truncate long files."""
    examples = []
    if not os.path.exists(dataset_dir):
        print(f"Warning: {dataset_dir} not found")
        return examples
    # Calculate keyword scores
    def calculate_keyword_score(content: str, primary_keywords: list, secondary_keywords: list) -> float:
        content_lower = content.lower()
        primary_score = sum(2 for keyword in primary_keywords if keyword.lower() in content_lower)
        secondary_score = sum(1 for keyword in secondary_keywords if keyword.lower() in content_lower)
        return (primary_score + secondary_score) / (len(content.split()) ** 0.5)
    # Walk through the dataset directory
    for root, _, files in os.walk(dataset_dir):
        for file in files:
            if file.endswith('.liquid'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Truncate content
                        content = truncate_content(content, max_lines)
                        # Calculate relevance score
                        score = calculate_keyword_score(
                            content,
                            keywords["primary_keywords"],
                            keywords["secondary_keywords"]
                        )
                        if score > 0:
                            # Determine file type and path
                            file_type = 'liquid'
                            if 'sections' in root:
                                relative_path = os.path.join('sections', file)
                            else:
                                relative_path = os.path.join('snippets', file)
                            examples.append({
                                "type": "implementation",
                                "file_path": relative_path,
                                "file_type": file_type,
                                "content": content,
                                "score": score
                            })
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    # Sort by score and limit to top examples
    examples.sort(key=lambda x: x["score"], reverse=True)
    return examples[:10]  # Return top 10 examples

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

async def generate_examples(sections_dir: str, section_number: int = None, output_dir: str = None, max_lines: int = 150):
    try:
        print("Reading dataset purposes...")
        dataset_purposes = await get_dataset_purposes()
        if not dataset_purposes:
            raise ValueError("No dataset purposes found")
        if section_number is not None:
            section_files = [(section_number, glob.glob(os.path.join(sections_dir, f"{section_number:02d}-*.md"))[0])]
        else:
            print("\nNo section number provided. Processing all section files...")
            section_files = get_all_section_files(sections_dir)
        for section_num, section_file in section_files:
            print(f"\nProcessing section {section_num}: {section_file}")
            design_docs = get_design_docs(sections_dir, section_num)
            if not design_docs:
                print(f"Warning: No design docs found for section {section_num}")
                continue
            print(f"\nAnalyzing design for section {section_num}...")
            analysis_data = await analyze_design_and_select_datasets(design_docs, dataset_purposes)
            if not analysis_data:
                print(f"Warning: Failed to analyze design for section {section_num}")
                continue
            base_dir = output_dir if output_dir else "examples"
            os.makedirs(base_dir, exist_ok=True)
            analysis_file = os.path.join(base_dir, f"{section_num:02d}-dataset_analysis.json")
            with open(analysis_file, "w", encoding="utf-8") as f:
                json.dump(analysis_data, f, indent=2)
            print(f"✓ Analysis saved to {analysis_file}")
            print(f"\nExtracting implementation examples for section {section_num}...")
            all_examples = []
            for dataset in analysis_data["datasets"]:
                dataset_dir = os.path.join("dataset", dataset["name"])
                examples = extract_code_examples_from_dataset(dataset_dir, dataset, max_lines=max_lines)
                if examples:
                    all_examples.extend(examples)
            if not all_examples:
                print(f"Warning: No relevant examples found for section {section_num}")
                continue
            examples_file = os.path.join(base_dir, f"{section_num:02d}-examples.txt")
            with open(examples_file, "w", encoding="utf-8") as f:
                f.write("IMPLEMENTATION EXAMPLES\n")
                f.write("=" * 50 + "\n\n")
                formatted_examples = [format_implementation_example(ex) for ex in all_examples]
                f.write("\n".join(formatted_examples))
            print(f"✓ Examples saved to {examples_file}")
        print("\n✅ All sections processed successfully!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def main():
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")
    import argparse
    parser = argparse.ArgumentParser(description="Generate theme examples from design documentation")
    parser.add_argument("--sections-dir", required=True, help="Directory containing parsed section markdown files")
    parser.add_argument("--section", type=int, help="Optional: Section number to generate examples for (e.g., 1 for 01-hero-section.md). If not provided, processes all sections.")
    parser.add_argument("--output-dir", required=True, help="Directory to save examples and analysis")
    parser.add_argument("--max-lines", type=int, default=150, help="Maximum number of lines to keep in each example file (default: 150)")
    args = parser.parse_args()
    await generate_examples(args.sections_dir, args.section, output_dir=args.output_dir, max_lines=args.max_lines)

if __name__ == "__main__":
    asyncio.run(main()) 