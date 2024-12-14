"""
This module extracts book URLs from a sitemap XML file.

It parses an XML file to find sitemap URLs related to books,
downloads the sitemaps (which are often gzipped), extracts the book URLs,
and saves them to an output file.
"""

import xml.etree.ElementTree as ET
import requests
import gzip
import io

def extract_livre_sitemaps(xml_file):
    """
    Extracts sitemap URLs that contain '/products/livre/' from an XML file.

    Args:
        xml_file (str): The path to the XML file.

    Returns:
        list: A list of sitemap URLs containing '/products/livre/'.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    livre_sitemaps = []
    
    for sitemap in root.findall('.//ns:sitemap', namespace):
        loc = sitemap.find('ns:loc', namespace)
        if loc is not None:
            url = loc.text
            if '/products/livre/' in url:
                livre_sitemaps.append(url)
    
    return livre_sitemaps

def download_and_extract_urls(sitemap_urls, output_file):
    """
    Downloads each sitemap, extracts book URLs, and saves them to a file.

    Args:
        sitemap_urls (list): A list of sitemap URLs to process.
        output_file (str): The path to the output file where URLs will be saved.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, headers=headers, timeout=60)
                if response.status_code == 200:
                    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
                        xml_content = gz.read()
                    
                    root = ET.fromstring(xml_content)
                    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                    
                    for url in root.findall('.//ns:url/ns:loc', namespace):
                        f.write(url.text + '\n')
                    
                    print(f"Processed {sitemap_url}")
                else:
                    print(f"Failed to download {sitemap_url}: Status code {response.status_code}")
                    
            except Exception as e:
                print(f"Error processing {sitemap_url}: {e}")

if __name__ == "__main__":
    try:
        sitemaps = extract_livre_sitemaps('products.xml')
        
        if sitemaps:
            print(f"Found {len(sitemaps)} livre sitemaps. Downloading and extracting URLs...")
            download_and_extract_urls(sitemaps, 'output/book_urls.txt')
            print("Completed! URLs have been saved to output/book_urls.txt")
        else:
            print("No livre sitemaps found in the file.")
            
    except Exception as e:
        print(f"Error: {e}")
