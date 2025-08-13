import os
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

# Initialize Anthropic client (aligned with existing scripts)
plan_llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature=0.1,
    max_tokens=20000
)

def read_plan(plan_path: str) -> str:
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"❌ Plan file not found at: {plan_path}")
    except Exception as e:
        raise RuntimeError(f"❌ Error reading plan file: {e}")

def build_system_prompt() -> str:
    return """
You are a Shopify Liquid architect. You will receive a previously generated multi-file offer page plan with implementation code blocks. Transform it into a single, production-ready Liquid template file at templates/page.offer.liquid by merging, adapting, and inlining the necessary code from the plan.

Goal:
- Produce ONE self-contained file: templates/page.offer.liquid
- The file must fully implement the offer page without depending on any external sections/snippets/assets beyond Shopify core objects

Scope and Responsibilities:
- Consolidate and adapt the plan's multi-file code (templates, sections, snippets) into a single Liquid template
- Inline CSS inside <style> and JS inside <script> tags
- Convert any references to snippets/sections into equivalent inline markup and logic

Critical Syntactical Rules (must follow):
1) Do NOT include {% schema %} blocks in the template
2) Do NOT include <html> or <body> tags in the template; use <div>, <section>, <style>, <script> as needed
3) All code MUST be contained in templates/page.offer.liquid only (no includes/renders to external snippets/sections)
4) Do NOT use filters inside tag parameters (e.g., no "limit: collection.products | size"). Perform calculations first using assign with unique variable names, then reference those variables in tags
5) Do NOT use limit as a filter within assign. limit is only valid as a for-loop parameter; to slice arrays outside a loop, use the slice filter
6) Do NOT include limit parameters inside if statements. It is not valid in conditions. Compute values separately and compare the variables
7) When retrieving the first item from a filtered collection, use the first filter instead of combining where with limit
8) Avoid localStorage; state should not rely on localStorage due to corruption across tabs
9) Ensure valid Liquid syntax compatible with Shopify 2.0 templates
10) Keep JavaScript in <script> and CSS in <style> inside the template file

Output Format (STRICT):
---
FILE: templates/page.offer.liquid
TYPE: liquid
CONTENT:
```liquid
[entire one-file implementation]
```
---

Notes:
- The output must contain exactly one code block following the format above
- The code must be complete, working, and readable without any additional files
- If the plan defines products/collections, integrate them responsibly (e.g., guard for missing data)
- Favor progressive enhancement and graceful error states
"""

def read_requirements(requirements_path: str = "offer_requirements_prompt.txt") -> str:
    try:
        with open(requirements_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        # Soft-fail: still proceed without requirements
        return ""
    except Exception:
        return ""

def build_user_prompt(plan_text: str, requirements_text: str) -> str:
    return f"""
Context:
Below are the original Offer Page Requirements that were used to generate the multi-file plan. Use them as grounding to preserve intent and resolve ambiguities.

Offer Page Requirements (Grounding):
{requirements_text}

Plan To Convert (source of truth):
Convert the following multi-file plan and its code blocks into a single, self-contained template, following the system instructions above. Do not regenerate a new plan—consolidate what is provided.

{plan_text}
"""

def convert_plan_to_one_file(plan_text: str) -> str:
    system_prompt = build_system_prompt()
    requirements_text = read_requirements()
    user_prompt = build_user_prompt(plan_text, requirements_text)
    messages = [
        HumanMessage(role="system", content=system_prompt),
        HumanMessage(role="user", content=user_prompt),
    ]
    resp = plan_llm.invoke(messages)
    return resp.content.strip()

def main():
    # Check for required environment variable
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise EnvironmentError("❌ ANTHROPIC_API_KEY must be set")

    plan_path = os.environ.get("PLAN_PATH", "offer_plan_claude.txt")
    output_path = os.environ.get("OUTPUT_PATH", "one_page_offer_from_plan.txt")

    plan_text = read_plan(plan_path)
    one_file_output = convert_plan_to_one_file(plan_text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(one_file_output)

    print(f"✅ One-file offer implementation saved to {output_path}")
    print("\nGenerated One-File Implementation:\n")
    print(one_file_output)

if __name__ == "__main__":
    main()

