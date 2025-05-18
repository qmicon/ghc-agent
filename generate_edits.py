#!/usr/bin/env python3
"""
generate_edits.py
-----------------------------------------------------------------
Generates suggested edits for Shopify codebase by:
1. Reading all files from claude_workspace
2. Creating a string representation of the codebase
3. Using Claude to analyze edit_prompt.txt and suggest edits
"""

import os
from pathlib import Path
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

# Initialize Claude
edit_llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature=0.1,
    max_tokens=10000
)

def read_codebase(workspace_dir: str = "claude_workspace") -> str:
    """Read all files from workspace and create a codebase string."""
    codebase = ["SHOPIFY CODEBASE:\n"]
    
    # Walk through the workspace directory
    for root, _, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith(('.liquid', '.json')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Get relative path from workspace directory
                        rel_path = os.path.relpath(file_path, workspace_dir)
                        # Add file to codebase string
                        codebase.append(f"{rel_path}\n```liquid\n{content}\n```\n")
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")

    with open("edit_codebase.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(codebase))
    return "\n".join(codebase)

def generate_edits(codebase: str, edit_prompt_path: str = "edit_prompt.txt") -> str:
    """Generate suggested edits using Claude."""
    # Read edit prompt
    try:
        with open(edit_prompt_path, "r", encoding="utf-8") as f:
            edit_prompt = f.read()
    except FileNotFoundError:
        print(f"❌ {edit_prompt_path} not found")
        return ""
    except Exception as e:
        print(f"❌ Error reading {edit_prompt_path}: {e}")
        return ""

    # System prompt with edit format rules
    system_prompt = """
    You are a Shopify theme developer specialized in making precise code edits.
    Analyze the edit prompt and the current codebase to suggest specific edits.

    Your task is to generate edits in the following format:

    path/to/file.ext
    ```
    <<<<<<< SEARCH
    [exact content to replace]
    =======
    [new content to insert]
    >>>>>>> REPLACE
    ```

    Critical rules for SEARCH/REPLACE blocks:
    1. SEARCH content must match exactly what's in the file:
       - Match character-for-character including whitespace, indentation, line endings
       - Include all comments, docstrings, etc.
    2. SEARCH/REPLACE blocks will ONLY replace the first match occurrence:
       - Include multiple unique SEARCH/REPLACE blocks if you need to make multiple changes
       - Include just enough lines in each SEARCH section to uniquely match each set of lines
       - List multiple SEARCH/REPLACE blocks in the order they appear in the file
    3. Keep SEARCH/REPLACE blocks concise:
       - Break large blocks into smaller ones that each change a small portion
       - Include just the changing lines and a few surrounding lines for uniqueness
       - Do not include long runs of unchanging lines
       - Each line must be complete (never truncate lines)
    4. Special operations:
       - To move code: Use two SEARCH/REPLACE blocks (delete + insert)
       - To delete code: Use empty REPLACE section

    Your response should:
    1. List all suggested edits in the format above
    2. Include a brief explanation for each edit
    3. Ensure all edits follow the critical rules
    4. Verify that SEARCH content exactly matches the codebase
    5. If required to generate a new file/asset, do that instead of trying to use something that is not in the codebase
    """

    # User prompt with codebase and edit request
    user_prompt = f"""
    Current Codebase:
    {codebase}

    Edit Request:
    {edit_prompt}

    Please suggest specific edits following the format and rules above.
    """

    # Get edits from Claude
    messages = [
        HumanMessage(role="system", content=system_prompt),
        HumanMessage(role="user", content=user_prompt)
    ]
    
    resp = edit_llm.invoke(messages)
    return resp.content.strip()

def main():
    # Check for required environment variable
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")

    # Generate codebase string
    print("Reading codebase...")
    codebase = read_codebase()
    if not codebase:
        print("❌ No files found in claude_workspace")
        return

    # Generate edits
    print("Generating edits...")
    edits = generate_edits(codebase)
    if not edits:
        print("❌ No edits generated")
        return

    # Save edits
    output_file = "suggested_edits.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(edits)
    print(f"✓ Edits saved to {output_file}")

if __name__ == "__main__":
    main() 