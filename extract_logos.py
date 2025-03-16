import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import urllib3
import re

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
			domain = url.split("//")[-1].split("/")[0].split(".")[0]
			img_name = os.path.basename(logo_url.split("?")[0])  # Remove query parameters if any
			filename = os.path.join(folder, f"{domain}.{img_name.split('.')[-1]}")
			with open(filename, 'wb') as f:
				for chunk in img_response.iter_content(chunk_size=1024):
					if chunk:
						f.write(chunk)
			# print(f"Downloaded logo for {url} to {filename}")
			return filename
		else:
			print(f"Failed to download image from {logo_url} (status code {img_response.status_code})")
			return None
	except Exception as e:
		print(f"Error processing {url}: {e}")
		return None
	
def exist_in_files(folder_files, key):
	for file in folder_files:
		if file.startswith(key):
			return True
	return False

df = pd.read_parquet('logos.snappy.parquet') 
# print(df)
folder = "logos"
formats = [".svg", ".png", ".jpg", ".jpeg", ".ico"]
os.makedirs(folder, exist_ok=True)
dublicates: dict[list] = {}

# many companies have multiple domains, so i check for dublicates
# i will take only the first part of the url (split by . - _ and only first 4 characters to identify a company)
# then i can check the file dublicates.txt if i dont recognize a company wrong as dublicate
for url in df['domain']:
	key = re.split(r'\-|\_|\.', url.split("/")[0])[0][:4]
	if not key in dublicates:
		dublicates[key] = [url]
	else:
		dublicates[key].append(url)

dublicates_nr, dublicates_company = 0, 0

dublicates_file = open("dublicates.txt", "w")
for key in dublicates.keys():
	if len(dublicates[key]) > 1:
		dublicates_file.write(f"{key} : {dublicates[key]}\n")
		dublicates_nr += len(dublicates[key])
		dublicates_company += 1
dublicates_file.write(f"Total number of dublicates: {dublicates_nr}\n")
dublicates_file.write(f"Total number of companies with dublicates: {dublicates_company}\n")
dublicates_file.write(f"Total number of companies (non dublicate): {len(dublicates)}\n")
dublicates_file.close()

success, failed, real_total = 0, 0, len(dublicates)
failed_companies = []
logos_files = os.listdir(folder)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
for key, company_domains in dublicates.items():
	succed = False
	existInFiles = exist_in_files(logos_files, key)
	for url in company_domains:
		if existInFiles or download_logo("http://" + url, folder):
			succed = True
			success += 1
			break
	if not succed:
		failed += 1
		failed_companies.append(company_domains)

print(f"Succesfully downloaded {success} logos for {real_total} companies ({failed} failed)")
print(f"Failed companies:")
for company_domains in failed_companies:
	print(company_domains)
