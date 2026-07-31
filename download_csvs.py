import os
import csv
import string
import requests
from bs4 import BeautifulSoup

# Define output folder in workspace
workspace_dir = os.path.dirname(os.path.abspath(__file__))
csv_folder = os.path.join(workspace_dir, "csv")

# Create folder if it doesn't exist
os.makedirs(csv_folder, exist_ok=True)

base_url = "https://www.accessdata.fda.gov/scripts/cder/psg/index.cfm"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print(f"Starting download of FDA PSG data into: {csv_folder}")

for letter in string.ascii_uppercase:
    print(f"Processing letter '{letter}'...", end="", flush=True)
    
    url = f"{base_url}?event=Home.Letter&searchLetter={letter}"
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f" Failed (HTTP status {response.status_code})")
            continue
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # The first table on the page contains the records for that letter
        table = soup.find("table")
        if not table:
            print(" No table found (possibly no records).")
            continue
            
        # Extract headers
        headers_row = table.find("tr")
        if not headers_row:
            print(" Empty table.")
            continue
            
        headers_text = []
        for th in headers_row.find_all(["th", "td"]):
            # Clean header text
            txt = th.get_text(strip=True)
            # Remove any duplicate spacing/newline artifacts
            txt = " ".join(txt.split())
            headers_text.append(txt)
            
        # Extract rows
        rows = table.find_all("tr")[1:]  # skip header row
        data_rows = []
        
        for row in rows:
            cols = row.find_all(["td", "th"])
            if not cols:
                continue
                
            row_data = []
            for col in cols:
                # If there is a link, get the text and URL
                link = col.find("a")
                if link and link.get("href"):
                    href = link.get("href")
                    # If it's a relative URL, make it absolute
                    if href.startswith("/"):
                        href = "https://www.accessdata.fda.gov" + href
                    elif not href.startswith("http"):
                        href = "https://www.accessdata.fda.gov/scripts/cder/psg/" + href
                    
                    # We will store the href as well if this column is the active ingredient
                    # The structure of the user CSV has separate URL column or combines them.
                    # Let's match the CSV format we saw in Rabeprazole's CSV:
                    # Column 1: "Active Ingredient (link to Specific Guidance)" -> active ingredient text
                    # Column 2: "URL" -> the link URL
                    # Let's build exactly that structure
                    txt = col.get_text(strip=True)
                    row_data.append(txt)
                    row_data.append(href)
                else:
                    txt = col.get_text(strip=True)
                    # Clean up spacing/whitespace
                    txt = " ".join(txt.split())
                    row_data.append(txt)
            
            # Ensure row has correct column count (7 columns in original CSV:
            # Active Ingredient, URL, Type, Route, Dosage Form, RLD or RS Number, Date Recommended)
            # But the HTML table has only 6 visual columns (since link is embedded in the Active Ingredient text).
            # So if we extracted text and URL, we have 7 elements, which matches the CSV perfectly.
            if len(row_data) == 7:
                data_rows.append(row_data)
            else:
                # Fallback if structure differs slightly
                data_rows.append(row_data)
                
        # Write to CSV file
        csv_file_path = os.path.join(csv_folder, f"{letter}.csv")
        with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            
            # Write headers: we need 7 headers to match the data format
            # e.g., ["Active Ingredient (link to Specific Guidance)", "URL", "Type", "Route", "Dosage Form", "RLD or RS Number", "Date Recommended"]
            # Let's construct it:
            csv_headers = [
                "Active Ingredient (link to Specific Guidance)",
                "URL",
                "Type",
                "Route",
                "Dosage Form",
                "RLD or RS Number",
                "Date Recommended"
            ]
            writer.writerow(csv_headers)
            writer.writerows(data_rows)
            
        print(f" Done ({len(data_rows)} records saved).")
        
    except Exception as e:
        print(f" Error: {e}")

print("All downloads finished.")
