# Usage: python get_shopify_page_url_from_sitemap.py <website> <page_type>
# Example: python get_shopify_page_url_from_sitemap.py marsghc.com Collection
# <website> should be canonical (e.g., marsghc.com)
# <page_type> can be one of: Home, Collection, Product, AllBlogs, SingleBlog

import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

def fetch_xml(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return ET.fromstring(resp.content)

def get_sitemap_urls(sitemap_url):
    root = fetch_xml(sitemap_url)
    return [loc.text for loc in root.findall('.//{*}loc')]

def get_page_url(website, page_type):
    base_url = f"https://{website}"
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    sitemap_urls = get_sitemap_urls(sitemap_url)

    # Helper to fetch first url from a sub-sitemap that contains a required substring
    def get_first_matching_from_submap(submap_url, required_substring=None):
        urls = get_sitemap_urls(submap_url)
        if required_substring:
            for url in urls:
                if required_substring in url:
                    return url
            return None
        return urls[0] if urls else None

    # Home page
    if page_type.lower() == "home":
        return base_url

    # Find sub-sitemaps
    collection_sitemap = next((u for u in sitemap_urls if "collection" in u), None)
    product_sitemap = next((u for u in sitemap_urls if "product" in u), None)
    blog_sitemap = next((u for u in sitemap_urls if "blog" in u and not u.endswith('.xml')), None)
    blog_sitemap_xml = next((u for u in sitemap_urls if "blog" in u and u.endswith('.xml')), None)

    if page_type.lower() == "collection":
        if collection_sitemap:
            return get_first_matching_from_submap(collection_sitemap, "/collections/")
        else:
            return None
    elif page_type.lower() == "product":
        if product_sitemap:
            return get_first_matching_from_submap(product_sitemap, "/products/")
        else:
            return None
    elif page_type.lower() in ["allblogs", "all_blogs", "all-blogs-list", "all_blogs_list"]:
        # Return the blog listing page by removing the last segment from the first blog post URL
        if blog_sitemap_xml:
            urls = get_sitemap_urls(blog_sitemap_xml)
            if urls:
                first_blog_url = urls[0]
                # Remove the last segment (post handle) to get the blog listing
                if first_blog_url.count('/') >= 4:
                    return '/'.join(first_blog_url.split('/')[:-1])
        return None
    elif page_type.lower() in ["singleblog", "single_blog", "single-blog"]:
        if blog_sitemap_xml:
            return get_first_matching_from_submap(blog_sitemap_xml, "/blogs/")
        else:
            return None
    else:
        return None

def main():
    if len(sys.argv) != 3:
        print("Usage: python get_shopify_page_url_from_sitemap.py <website> <page_type>")
        print("<page_type> can be one of: Home, Collection, Product, AllBlogs, SingleBlog")
        sys.exit(1)

    website = sys.argv[1]
    page_type = sys.argv[2]
    url = get_page_url(website, page_type)
    if url:
        print(f"URL for {page_type} on {website}: {url}")
    else:
        print(f"Could not find URL for {page_type} on {website}.")

if __name__ == "__main__":
    main() 