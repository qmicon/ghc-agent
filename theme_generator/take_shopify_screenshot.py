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

def get_all_section_ids(url, form_factor):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        if form_factor == "mobile":
            page.set_viewport_size({"width": 360, "height": 800})
        elif form_factor == "desktop":
            page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(url)
        # Wait for at least one section to appear (wait for attachment, not visibility)
        page.wait_for_selector('[id^="shopify-section-"]', state='attached', timeout=5000)
        
        # Scroll to bottom to load all sections, then back to top
        scroll_to_bottom(page)
        
        elements = page.query_selector_all('[id^="shopify-section-"]')
        section_ids = [element.get_attribute("id") for element in elements]
        browser.close()
        return section_ids

def main():
    parser = argparse.ArgumentParser(description="Take screenshots of a Shopify site by section.")
    parser.add_argument("website_url", help="Canonical website URL (e.g., abc.com)")
    parser.add_argument("form_factor", choices=["mobile", "desktop"], help="Form factor: mobile or desktop")
    parser.add_argument("--output-dir", default="screenshots", help="Base output directory (default: screenshots)")
    parser.add_argument("--save-selector-code", action="store_true", help="Save selector code alongside screenshots")
    args = parser.parse_args()

    website_url = args.website_url
    form_factor = args.form_factor
    output_dir = args.output_dir
    save_selector_code = args.save_selector_code

    base_url = f"https://{website_url}"
    section_ids = get_all_section_ids(base_url, form_factor)
    if not section_ids:
        print("No Shopify section elements found.")
        sys.exit(0)

    os.makedirs(output_dir, exist_ok=True)

    for idx, el_id in enumerate(section_ids, 1):
        print(f"Element {idx}: {el_id}")
        screenshot_path = os.path.join(output_dir, f"{str(idx).zfill(2)}-{el_id}.png")
        try:
            element_html = capture_element_screenshot(
                url=base_url,
                selector=f"#{el_id}",
                screenshot_path=screenshot_path,
                form_factor=form_factor
            )
            print(f"Saved screenshot: {screenshot_path}")
            
            # Save selector code if requested
            if save_selector_code:
                selector_code_path = os.path.join(output_dir, f"{str(idx).zfill(2)}-{el_id}.txt")
                with open(selector_code_path, 'w', encoding='utf-8') as f:
                    f.write(element_html)
                print(f"Saved element HTML: {selector_code_path}")
                
        except Exception as e:
            print(f"{str(idx)} {el_id} could not be saved (possibly hidden section): {e}")

if __name__ == "__main__":
    main() 