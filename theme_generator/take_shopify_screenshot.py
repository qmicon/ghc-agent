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
        element = page.wait_for_selector(selector, timeout=5000)
        element.scroll_into_view_if_needed()
        time.sleep(2)
        element = page.query_selector(selector)
        element.screenshot(path=screenshot_path)
        browser.close()

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
        elements = page.query_selector_all('[id^="shopify-section-"]')
        section_ids = [element.get_attribute("id") for element in elements]
        browser.close()
        return section_ids

def main():
    parser = argparse.ArgumentParser(description="Take screenshots of a Shopify site by section.")
    parser.add_argument("website_url", help="Canonical website URL (e.g., abc.com)")
    parser.add_argument("form_factor", choices=["mobile", "desktop"], help="Form factor: mobile or desktop")
    parser.add_argument("--output-dir", default="screenshots", help="Base output directory (default: screenshots)")
    args = parser.parse_args()

    website_url = args.website_url
    form_factor = args.form_factor
    output_dir = args.output_dir

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
            capture_element_screenshot(
                url=base_url,
                selector=f"#{el_id}",
                screenshot_path=screenshot_path,
                form_factor=form_factor
            )
            print(f"Saved screenshot: {screenshot_path}")
        except Exception as e:
            print(f"{str(idx)} {el_id} could not be saved (possibly hidden section): {e}")

if __name__ == "__main__":
    main() 