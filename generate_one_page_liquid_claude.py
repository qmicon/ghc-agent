import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from langchain_anthropic import ChatAnthropic  
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

# Initialize Azure OpenAI LLM
plan_llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",  # More powerful model for complex planning
    temperature=0.1,
    max_tokens=20000 # Enough tokens for a multi-step plan
)

def load_examples():
    """Load examples from examples.txt file."""
    try:
        with open("examples.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: examples.txt not found")
        return ""
    except Exception as e:
        print(f"Warning: Error reading examples.txt: {e}")
        return ""

async def fetch_shopify_data(shopify_url):
    """Fetch collections and products from Shopify store."""
    async with aiohttp.ClientSession() as session:
        # Fetch collections
        collections_url = f"{shopify_url.rstrip('/')}/collections.json"
        async with session.get(collections_url) as response:
            collections = await response.json()
        
        # Fetch products
        products_url = f"{shopify_url.rstrip('/')}/products.json"
        async with session.get(products_url) as response:
            products = await response.json()
        
        return {
            "collections": collections.get("collections", []),
            "products": products.get("products", [])
        }

async def generate_offer_plan(shopify_url):
    # Fetch store data
    store_data = await fetch_shopify_data(shopify_url)
    
    # Get first collection and product for example
    collection = store_data["collections"][-1] if store_data["collections"] else None
    product = store_data["products"][0] if store_data["products"] else None
    
    # Load examples
    examples = load_examples()
    try:
        with open("offer_requirements_prompt.txt", "r", encoding="utf-8") as f:
            offer_requirements = f.read()
    except FileNotFoundError:
        print("❌ offer_requirements_prompt.txt not found")
        return
    except Exception as e:
        print(f"❌ Error reading offer_requirements_prompt.txt: {e}")
        return
    
    # Define requirements with actual data
    requirements = f"""
    {offer_requirements}
      
    Store Data that can be used for the offer page:
    - Collection Handle: {collection['handle'] if collection else 'No collections found'}
    - Product Handle: {product['handle'] if product else 'No products found'}

    Current Date and Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    # Build prompts
    system_prompt = """
    You are a Shopify Liquid architect specialized in designing high-impact landing pages for promotional offers.
    Create a complete offer page implementation from scratch.

    Your task is to create a detailed implementation plan that includes:
    1. Step-by-step implementation guide
    2. Detailed implementation instructions
    3. Actual code block that follows the implementation instructions

    Required File Structure:
    - templates/page.offer.liquid (main template with all the code)

    Focus on:
    - Clear component structure
    - Modern, responsive design
    - User-friendly interface
    - Step-by-step implementation details
    - Proper error handling and validation

    Technical Requirements:
    - Must work with Shopify 2.0 architecture
    - Use liquid templates for page structure
    - Create all components from scratch
    - Implement modern, responsive design
    - Include proper error handling and validation
    - Use the provided collection handle or product handle if required

    Required File Structure:
    1. templates/page.offer.liquid
       - Must define all sections in the correct order
       - Must be valid liquid format
       - Must contain all the code for the offer page

    Please provide a detailed written plan that includes:

    1. Implementation Steps
    - Step-by-step guide on how to implement the offer page
    - Order of implementation
    - Dependencies between components

    2. Implementation Notes
    - Detailed description of implementation notes for the template code
    - Explain the logic and reasoning behind the implementation code
    - Explain architecture decisions and trade-offs
    - Document error handling strategy

    After the plan is generated, generate the code while following these instructions:

    1. The code follows modern web development best practices and patterns
    2. Components are well-structured and maintainable
    3. User interactions are handled efficiently and reliably
    4. Error cases are handled gracefully
    5. avoid using local storage as states get corrupted when the page is loaded in a new tab
    6. All the code should be in the templates/page.offer.liquid file

    CRITICAL INSTRUCTION: A plan should contain all the detailed information so that a beginner Shopify developer could save the implementation to files and it would work without any additional guidance.

    CRITICAL INSTRUCTION FOR CODE BLOCKS OUTPUT FORMAT: When showing implementation code, follow this exact format:
    ---
    FILE: [exact file path]
    TYPE: [liquid|json|javascript|css]
    CONTENT:
    ```<type>
    [actual code content]
    ```
    ---  

    Output Format Example 1:
    ---
    FILE: templates/page.offer.liquid
    TYPE: liquid
    CONTENT:
    ```liquid
    {{% section 'header' %}}
    ```
    ---

    Following this format is very important as the beginner developer is using a regex tool to extract the code blocks and save them to correct file paths.

    CRITICAL VALIDATION INSTRUCTIONS:
    1. liquid templates under templates/ must have all code according to the requirements.
    2. Do not use filters (e.g., | times) directly within tag parameters like limit in for loops or conditions in if statements. Instead, perform calculations separately using the assign tag with unique variable names, then reference the resulting variable within your tags.
    3. Do not use limit as a filter within assign statements. The limit keyword is a parameter for for loops, not a filter. To limit the number of items in an array outside of a loop, use the slice filter
    4. Do not include limit parameters within if statements. The limit parameter is not valid in this context and will cause syntax errors.
    5. When you need to retrieve the first item from a filtered collection, use the first filter instead of combining where with limit.
    6. Dont put <html> tag as its not valid in liquid file, other tags like <div>, <style>, <section>, etc. can be used
    7. dont put {% schema %} in the code

    Below are some examples of how the code developed by shopify developers looks like, it has two types of examples:
    1. OFFER PAGE IMPLEMENTATION CODE EXAMPLES: Complete implementation examples from similar offer pages, showing the structure and patterns used in production.
    2. RELEVANT CODE EXAMPLES FOR UI COMPONENTS: Reusable UI components and patterns that can be adapted for the offer requirements.

    Use these examples as reference for:
    - Component architecture and patterns
    - Implementation approaches
    - Best practices for Shopify theme development

    Do not copy the examples directly - instead, understand the patterns and adapt them to the mentioned requirements.

    {examples}
    """

    user_prompt = f"""
    Offer Page Requirements:
    {requirements}
    """

    messages = [
        HumanMessage(role="system", content=system_prompt),
        HumanMessage(role="user", content=user_prompt),
    ]

    # Generate plan
    resp = await plan_llm.ainvoke(messages)
    content = resp.content.strip()
    
    # Save the plan
    output_file = "offer_plan_claude.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Plan saved to {output_file}")
    print("\nGenerated Plan:")
    print(content)

# Run and output the structured plan
if __name__ == "__main__":
    required_env_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT"
    ]
    
    missing_vars = [var for var in required_env_vars if var not in os.environ]
    if missing_vars:
        raise EnvironmentError(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    
    shopify_url = "https://test-wardrobe-ecomm.myshopify.com/"
    asyncio.run(generate_offer_plan(shopify_url)) 