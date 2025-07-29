# pip install playwright
# playwright install chromium

# Usage: python take_shopify_screenshot.py <website_url> <form_factor> [--output-dir OUTPUT_DIR]
# Example: python take_shopify_screenshot.py marsghc.com mobile
# <website_url> should be canonical (e.g., abc.com), <form_factor> can be one of ['mobile', 'desktop']

from playwright.sync_api import sync_playwright
import time
import sys
import os
import argparse
import re

def capture_element_screenshot(url, selector, screenshot_path, form_factor):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        if form_factor == "mobile":
            page.set_viewport_size({"width": 360, "height": 800})
        elif form_factor == "desktop":
            page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(url)
        
        # Wait for the element to be attached to the DOM
        element = page.wait_for_selector(selector, state='attached', timeout=5000)
        
        # Scroll the element into view
        element.scroll_into_view_if_needed()
        
        # Wait for the element to be visible after scrolling
        page.wait_for_selector(selector, state='visible', timeout=5000)
        
        # Additional wait for any animations or lazy loading
        time.sleep(2)
        
        # Take the screenshot
        element = page.query_selector(selector)
        element.screenshot(path=screenshot_path)
        # Get the outer HTML of the element
        element_html = element.evaluate('el => el.outerHTML')
        browser.close()
        return element_html

def scroll_to_bottom(page):
    """Scroll to the bottom of the page to load all content."""
    # Scroll to bottom
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)  # Wait for any lazy-loaded content
    # Scroll back to top
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)  # Brief pause after scrolling back

def get_all_elements_with_classes(url, form_factor, element_type='section'):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        if form_factor == "mobile":
            page.set_viewport_size({"width": 360, "height": 800})
        elif form_factor == "desktop":
            page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(url)
        
        # Scroll to bottom to load all content, then back to top
        scroll_to_bottom(page)
        
        element_data = []
        
        # Priority 1: Try shopify-section-template elements
        print("Checking for shopify-section-template elements...")
        template_elements = page.query_selector_all('[id^="shopify-section-template"]')
        if template_elements:
            print(f"Found {len(template_elements)} shopify-section-template elements")
            for element in template_elements:
                class_attr = element.get_attribute("class")
                id_attr = element.get_attribute("id")
                if class_attr:
                    classes = class_attr.strip().split()
                    selector = f"#{id_attr}.{'.'.join(classes)}"
                else:
                    classes = []
                    selector = f"#{id_attr}"
                
                element_data.append({
                    'classes': classes,
                    'class_string': class_attr or '',
                    'selector': selector,
                    'tag_name': element.evaluate('el => el.tagName.toLowerCase()'),
                    'id': id_attr,
                    'type': 'shopify-section-template'
                })
            return element_data
        
        # Priority 2: Try shopify-section elements
        print("Checking for shopify-section elements...")
        shopify_elements = page.query_selector_all('[id^="shopify-section"]')
        if shopify_elements:
            print(f"Found {len(shopify_elements)} shopify-section elements")
            for element in shopify_elements:
                class_attr = element.get_attribute("class")
                id_attr = element.get_attribute("id")
                if class_attr:
                    classes = class_attr.strip().split()
                    selector = f"#{id_attr}.{'.'.join(classes)}"
                else:
                    classes = []
                    selector = f"#{id_attr}"
                
                element_data.append({
                    'classes': classes,
                    'class_string': class_attr or '',
                    'selector': selector,
                    'tag_name': element.evaluate('el => el.tagName.toLowerCase()'),
                    'id': id_attr,
                    'type': 'shopify-section'
                })
            return element_data
        
        # Priority 3: Try regular section elements
        print("Checking for regular section elements...")
        # Wait for at least one section to appear
        page.wait_for_selector('section', state='attached', timeout=5000)
        section_elements = page.query_selector_all('section')
        if section_elements:
            print(f"Found {len(section_elements)} regular section elements")
            for element in section_elements:
                class_attr = element.get_attribute("class")
                id_attr = element.get_attribute("id")
                if class_attr:
                    classes = class_attr.strip().split()
                    if id_attr:
                        selector = f"section#{id_attr}.{'.'.join(classes)}"
                    else:
                        selector = f"section.{'.'.join(classes)}"
                else:
                    classes = []
                    if id_attr:
                        selector = f"section#{id_attr}"
                    else:
                        # For sections without id or class, use nth-child
                        selector = f"section:nth-child({len(element_data) + 1})"
                
                element_data.append({
                    'classes': classes,
                    'class_string': class_attr or '',
                    'selector': selector,
                    'tag_name': element.evaluate('el => el.tagName.toLowerCase()'),
                    'id': id_attr,
                    'type': 'regular-section'
                })
            return element_data
        
        browser.close()
        return element_data

def sanitize_filename(filename):
    """Sanitize filename by replacing invalid characters."""
    # Replace spaces and special characters with hyphens
    sanitized = re.sub(r'[^\w\-_.]', '-', filename)
    # Remove multiple consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    return sanitized

def main():
    parser = argparse.ArgumentParser(description="Take screenshots of elements with unique class values.")
    parser.add_argument("website_url", help="Canonical website URL (e.g., abc.com)")
    parser.add_argument("form_factor", choices=["mobile", "desktop"], help="Form factor: mobile or desktop")
    parser.add_argument("--output-dir", default="screenshots", help="Base output directory (default: screenshots)")
    parser.add_argument("--save-selector-code", action="store_true", help="Save selector code alongside screenshots")
    parser.add_argument("--element-type", default="section", help="Element type to capture (default: section)")
    args = parser.parse_args()

    website_url = args.website_url
    form_factor = args.form_factor
    output_dir = args.output_dir
    save_selector_code = args.save_selector_code
    element_type = args.element_type

    base_url = f"https://{website_url}"
    element_data = get_all_elements_with_classes(base_url, form_factor, element_type)
    
    if not element_data:
        print(f"No {element_type} elements found with any of the detection methods.")
        sys.exit(0)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Group elements by their class combination to avoid duplicates
    unique_elements = {}
    for data in element_data:
        # Create a unique key based on type, id, and classes
        if data['type'] in ['shopify-section-template', 'shopify-section']:
            # For Shopify sections, use id as primary key
            unique_key = f"{data['type']}_{data['id']}"
        else:
            # For regular sections, use class combination
            class_key = ' '.join(sorted(data['classes'])) if data['classes'] else 'no-class'
            unique_key = f"{data['type']}_{class_key}"
        
        if unique_key not in unique_elements:
            unique_elements[unique_key] = data

    print(f"\nFound {len(unique_elements)} unique {element_type} elements:")
    print(f"Section type: {element_data[0]['type']}")

    for idx, (unique_key, data) in enumerate(unique_elements.items(), 1):
        # Create display name based on section type
        if data['type'] in ['shopify-section-template', 'shopify-section']:
            display_name = f"{data['id']}"
            if data['class_string']:
                display_name += f" ({data['class_string']})"
        else:
            display_name = data['class_string'] if data['class_string'] else f"section-{idx}"
        
        print(f"Element {idx}: {display_name}")
        
        # Create a safe filename
        if data['type'] in ['shopify-section-template', 'shopify-section']:
            safe_filename = sanitize_filename(data['id'])
        else:
            safe_filename = sanitize_filename(data['class_string']) if data['class_string'] else f"section-{idx}"
        
        screenshot_path = os.path.join(output_dir, f"{str(idx).zfill(2)}-{safe_filename}.png")
        
        try:
            element_html = capture_element_screenshot(
                url=base_url,
                selector=data['selector'],
                screenshot_path=screenshot_path,
                form_factor=form_factor
            )
            print(f"Saved screenshot: {screenshot_path}")
            
            # Save selector code if requested
            if save_selector_code:
                selector_code_path = os.path.join(output_dir, f"{str(idx).zfill(2)}-{safe_filename}.txt")
                with open(selector_code_path, 'w', encoding='utf-8') as f:
                    f.write(f"Section Type: {data['type']}\n")
                    f.write(f"Selector: {data['selector']}\n")
                    if data['id']:
                        f.write(f"ID: {data['id']}\n")
                    f.write(f"Classes: {data['class_string']}\n")
                    f.write(f"Tag: {data['tag_name']}\n")
                    f.write("-" * 50 + "\n")
                    f.write(element_html)
                print(f"Saved element HTML: {selector_code_path}")
                
        except Exception as e:
            print(f"{str(idx)} {display_name} could not be saved (possibly hidden element): {e}")

if __name__ == "__main__":
    main() 