import os
import time
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
import json

class WebsiteScreenshotter:
    def __init__(self, base_output_dir="screenshots"):
        """Initialize the screenshotter with base output directory."""
        self.base_output_dir = base_output_dir
        self._ensure_base_dir()
        self.driver = None
        # Default viewport size
        self.default_viewport = (1920, 1080)

    def _ensure_base_dir(self):
        """Create base output directory if it doesn't exist."""
        if not os.path.exists(self.base_output_dir):
            os.makedirs(self.base_output_dir)

    def _get_website_dir(self, url):
        """Get the website-specific directory path."""
        domain = urlparse(url).netloc.replace(".", "_")
        website_dir = os.path.join(self.base_output_dir, domain)
        if not os.path.exists(website_dir):
            os.makedirs(website_dir)
        return website_dir

    def _get_viewport_dir(self, website_dir):
        """Get the viewport directory path using default size."""
        viewport_name = f"default_{self.default_viewport[0]}x{self.default_viewport[1]}"
        viewport_dir = os.path.join(website_dir, viewport_name)
        if not os.path.exists(viewport_dir):
            os.makedirs(viewport_dir)
        return viewport_dir

    def _setup_driver(self):
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--window-size={self.default_viewport[0]},{self.default_viewport[1]}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--hide-scrollbars")  # Hide scrollbars for cleaner screenshots

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def _get_full_page_height(self):
        """Get the full page height using JavaScript."""
        return self.driver.execute_script("""
            return Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.offsetHeight,
                document.body.clientHeight,
                document.documentElement.clientHeight
            );
        """)

    def _scroll_and_capture(self, url, viewport_dir):
        """Scroll through the page and capture screenshots."""
        try:
            if not self.driver:
                self._setup_driver()

            # Load the page
            self.driver.get(url)
            time.sleep(2)  # Initial wait for page load

            # Get page dimensions
            total_height = self._get_full_page_height()
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Calculate number of screenshots needed
            num_screenshots = (total_height + viewport_height - 1) // viewport_height
            
            # Take screenshots while scrolling
            screenshots_info = []
            for i in range(num_screenshots):
                # Scroll to position
                scroll_position = i * viewport_height
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(0.5)  # Wait for any lazy-loaded content

                # Take screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{i+1:03d}_{timestamp}.png"
                filepath = os.path.join(viewport_dir, filename)
                
                self.driver.save_screenshot(filepath)
                screenshots_info.append({
                    "filename": filename,
                    "scroll_position": scroll_position,
                    "viewport_height": viewport_height
                })
                
                print(f"Saved screenshot {i+1}/{num_screenshots}: {filepath}")

            # Save metadata about the screenshots
            metadata = {
                "url": url,
                "viewport_size": self.default_viewport,
                "total_height": total_height,
                "viewport_height": viewport_height,
                "num_screenshots": num_screenshots,
                "screenshots": screenshots_info,
                "timestamp": datetime.now().isoformat()
            }
            
            metadata_path = os.path.join(viewport_dir, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return viewport_dir

        except Exception as e:
            print(f"Error taking screenshots: {str(e)}")
            return None

    def take_screenshots(self, url):
        """
        Take full-page screenshots of the specified URL using default viewport size.
        
        Args:
            url (str): The URL to screenshot
        """
        website_dir = self._get_website_dir(url)
        viewport_dir = self._get_viewport_dir(website_dir)
        
        try:
            result = self._scroll_and_capture(url, viewport_dir)
            return result if result else None
        finally:
            self.close()

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Take screenshots of a website")
    parser.add_argument("url", help="URL of the website to screenshot")
    parser.add_argument("--output", "-o", default="screenshots", help="Base output directory (default: screenshots)")
    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'https://' + args.url

    # Take screenshots
    screenshotter = WebsiteScreenshotter(base_output_dir=args.output)
    result = screenshotter.take_screenshots(args.url)
    
    if result:
        print(f"\n✅ Screenshots saved to: {result}")
    else:
        print("\n❌ Failed to take screenshots")

if __name__ == "__main__":
    main() 