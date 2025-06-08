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
    """Extract section number from filename (e.g., '1-hero-section.md' -> 1)."""
    match = re.match(r'^(\d+)-', os.path.basename(section_file))
    if not match:
        raise ValueError(f"Invalid section filename format: {section_file}. Must start with a number followed by a hyphen.")
    return int(match.group(1))

def _find_section_file(website: str, viewport: str, section_number: int) -> str:
    """Find the section file that starts with the given number."""
    if section_number < 1:
        raise ValueError("Section number must be positive")
        
    sections_dir = os.path.join("screenshots", website, viewport, "design_docs", "sections")
    if not os.path.exists(sections_dir):
        raise FileNotFoundError(f"Sections directory not found: {sections_dir}")
    
    # Look for files starting with the section number
    pattern = f"{section_number:02d}-*.md"
    matching_files = glob.glob(os.path.join(sections_dir, pattern))
    
    if not matching_files:
        raise FileNotFoundError(f"No section file found starting with {section_number}- in {sections_dir}")
    if len(matching_files) > 1:
        raise ValueError(f"Multiple section files found starting with {section_number}- in {sections_dir}")
        
    return os.path.basename(matching_files[0])

def get_design_docs(website: str, viewport: str, section_number: int = None) -> str:
    """Get design documentation for a specific website, viewport, and optionally a specific section."""
    design_docs = []
    
    # Path to the design docs directory
    docs_dir = os.path.join("screenshots", website, viewport, "design_docs")
    if not os.path.exists(docs_dir):
        raise FileNotFoundError(f"Design docs not found for {website}/{viewport}")
    
    if section_number is not None:
        # Get specific section file
        section_file = _find_section_file(website, viewport, section_number)
        section_path = os.path.join(docs_dir, "sections", section_file)
        try:
            with open(section_path, "r", encoding="utf-8") as f:
                design_docs.append({
                    "filename": section_file,
                    "content": f.read()
                })
        except Exception as e:
            print(f"Warning: Could not read {section_path}: {e}")
    else:
        # Get all markdown files
        md_files = sorted(Path(docs_dir).glob("*_design.md"))
        for md_file in md_files:
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    design_docs.append({
                        "filename": md_file.name,
                        "content": f.read()
                    })
            except Exception as e:
                print(f"Warning: Could not read {md_file}: {e}")
    
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

def extract_code_examples_from_dataset(dataset_dir: str, keywords: dict) -> list:
    """Extract code examples from dataset directory based on keywords."""
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
            if file.endswith(('.liquid', '.json')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        # Calculate relevance score
                        score = calculate_keyword_score(
                            content,
                            keywords["primary_keywords"],
                            keywords["secondary_keywords"]
                        )
                        
                        if score > 0:
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

def get_all_section_files(website: str, viewport: str) -> list:
    """Get all section files from the sections directory."""
    sections_dir = os.path.join("screenshots", website, viewport, "design_docs", "sections")
    if not os.path.exists(sections_dir):
        raise FileNotFoundError(f"Sections directory not found: {sections_dir}")
    
    # Get all markdown files and sort them by section number
    section_files = []
    for file in glob.glob(os.path.join(sections_dir, "*.md")):
        try:
            section_number = get_section_number(file)
            section_files.append((section_number, os.path.basename(file)))
        except ValueError as e:
            print(f"Warning: {e}")
    
    # Sort by section number
    section_files.sort(key=lambda x: x[0])
    return section_files

async def generate_examples(website: str, viewport: str, section_number: int = None):
    """Generate examples based on design docs and dataset analysis."""
    try:
        # Get dataset purposes
        print("Reading dataset purposes...")
        dataset_purposes = await get_dataset_purposes()
        if not dataset_purposes:
            raise ValueError("No dataset purposes found")
        
        # Get section files to process
        if section_number is not None:
            section_files = [(section_number, _find_section_file(website, viewport, section_number))]
        else:
            print("\nNo section number provided. Processing all section files...")
            section_files = get_all_section_files(website, viewport)
        
        # Process each section
        for section_num, section_file in section_files:
            print(f"\nProcessing section {section_num}: {section_file}")
            
            # Get design docs for this section
            design_docs = get_design_docs(website, viewport, section_num)
            if not design_docs:
                print(f"Warning: No design docs found for section {section_num}")
                continue
            
            # Analyze design and select datasets
            print(f"\nAnalyzing design for section {section_num}...")
            analysis_data = await analyze_design_and_select_datasets(design_docs, dataset_purposes)
            if not analysis_data:
                print(f"Warning: Failed to analyze design for section {section_num}")
                continue
            
            # Create examples directory structure
            examples_dir = os.path.join("screenshots", website, viewport, "design_docs", "examples")
            os.makedirs(examples_dir, exist_ok=True)
            
            # Save analysis results
            analysis_file = os.path.join(examples_dir, f"{section_num:02d}-dataset_analysis.json")
            with open(analysis_file, "w", encoding="utf-8") as f:
                json.dump(analysis_data, f, indent=2)
            print(f"✓ Analysis saved to {analysis_file}")
            
            # Extract and format examples
            print(f"\nExtracting implementation examples for section {section_num}...")
            all_examples = []
            for dataset in analysis_data["datasets"]:
                dataset_dir = os.path.join("dataset", dataset["name"])
                examples = extract_code_examples_from_dataset(dataset_dir, dataset)
                if examples:
                    all_examples.extend(examples)
            
            if not all_examples:
                print(f"Warning: No relevant examples found for section {section_num}")
                continue
            
            # Save examples
            examples_file = os.path.join(examples_dir, f"{section_num:02d}-examples.txt")
            with open(examples_file, "w", encoding="utf-8") as f:
                # Write implementation examples
                f.write("IMPLEMENTATION EXAMPLES\n")
                f.write("=" * 50 + "\n\n")
                formatted_examples = [format_implementation_example(ex) for ex in all_examples]
                f.write("\n".join(formatted_examples))
            
            print(f"✓ Examples saved to {examples_file}")
        
        print("\n✅ All sections processed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def main():
    # Check for required environment variables
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")
    
    # Set up argument parser
    import argparse
    parser = argparse.ArgumentParser(description="Generate theme examples from design documentation")
    parser.add_argument("--website", required=True, help="Website directory name")
    parser.add_argument("--viewport", required=True, help="Viewport directory name")
    parser.add_argument("--section", type=int, help="Optional: Section number to generate examples for (e.g., 1 for 1-hero-section.md). If not provided, processes all sections.")
    args = parser.parse_args()
    
    await generate_examples(args.website, args.viewport, args.section)

if __name__ == "__main__":
    asyncio.run(main()) 