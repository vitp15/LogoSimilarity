import os
import re
import urllib3
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# Disable SSL warnings (because we use verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_logo(url, folder):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    try:
        # Request the webpage content
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code != 200:
            print(f"Failed to access {url} (status code {response.status_code})")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        # Try to find an <img> tag that contains "logo" in its alt or src attribute
        logo_img = None
        for img in soup.find_all('img'):
            alt_text = img.get('alt', '').lower()
            src = img.get('src', '')
            if 'logo' in alt_text or 'logo' in src.lower():
                logo_img = src
                break

        # If no logo is found, try to fall back to the favicon (if available)
        if not logo_img:
            icon_link = soup.find("link", rel=lambda x: x and 'icon' in x.lower())
            if icon_link:
                logo_img = icon_link.get('href')
            else:
                print(f"No logo or favicon found for {url}")
                return None

        # Convert relative URLs to absolute URLs
        logo_url = urljoin(url, logo_img)
        # Download the logo image
        img_response = requests.get(logo_url, headers=headers, stream=True, timeout=10, verify=False)
        if img_response.status_code == 200:
            # Create a filename based on the domain and image filename
            domain = url.split("//")[-1].split("/")[0]
            img_name = os.path.basename(logo_url.split("?")[0])  # Remove query parameters if any
            filename = os.path.join(folder, f"{domain}.{img_name.split('.')[-1]}")
            with open(filename, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return filename
        else:
            print(f"Failed to download image from {logo_url} (status code {img_response.status_code})")
            return None
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

def process_url(url, folder, logos_files):
    # Check if URL (or its corresponding file based on domain) already exists in folder
    if url in logos_files:
        return True  # already exists
    return bool(download_logo("http://" + url, folder))

def extract_logos(parquet="logos.snappy.parque", folder="logos"):
    df = pd.read_parquet(parquet).drop_duplicates(subset=['domain'])
    os.makedirs(folder, exist_ok=True)
    
    # Get existing logo files (splitting on '.' for a simple check)
    logos_files = [".".join(x.split(".")[:-1]) for x in os.listdir(folder)]
    
    success, failed, total = 0, 0, len(df['domain'])
    failed_companies = []
    
    # Use ThreadPoolExecutor for concurrent downloads.
    with ThreadPoolExecutor(max_workers=16) as executor:
        # Submit a future for each URL in the dataframe
        future_to_url = {executor.submit(process_url, url, folder, logos_files): url for url in df['domain']}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    success += 1
                else:
                    failed += 1
                    failed_companies.append(url)
            except Exception as exc:
                print(f"{url} generated an exception: {exc}")
                failed += 1
                failed_companies.append(url)
    
    print(f"Successfully downloaded logos for {success} out of {total} companies ({failed} failed)")
    print("Failed companies:", failed_companies)
