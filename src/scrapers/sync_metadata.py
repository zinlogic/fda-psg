import os
import csv
import string
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

# Obtener configuraciones de .env o usar valores por defecto
FDA_BASE_URL = os.getenv("FDA_BASE_URL", "https://www.accessdata.fda.gov/scripts/cder/psg/index.cfm")
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

def get_fda_psg_metadata(letter):
    """
    Scrapes the FDA PSG page for a specific letter and returns a list of metadata dictionaries.
    """
    url = f"{FDA_BASE_URL}?event=Home.Letter&searchLetter={letter}"
    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"Error fetching letter {letter}: HTTP {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")[1:]  # Skip header row
        data = []

        for row in rows:
            cols = row.find_all(["td", "th"])
            if not cols:
                continue

            row_data = {}
            # We expect the table to have columns:
            # 1. Active Ingredient (contains a link)
            # 2. Type
            # 3. Route
            # 4. Dosage Form
            # 5. RLD or RS Number
            # 6. Date Recommended
            
            # Extract link and Active Ingredient
            active_ingredient_col = cols[0]
            link = active_ingredient_col.find("a")
            row_data["active_ingredient"] = active_ingredient_col.get_text(strip=True)
            
            if link and link.get("href"):
                href = link.get("href")
                if href.startswith("/"):
                    row_data["pdf_url"] = "https://www.accessdata.fda.gov" + href
                elif not href.startswith("http"):
                    row_data["pdf_url"] = "https://www.accessdata.fda.gov/scripts/cder/psg/" + href
                else:
                    row_data["pdf_url"] = href
            else:
                row_data["pdf_url"] = ""

            # Extract remaining columns
            row_data["type"] = cols[2].get_text(strip=True) if len(cols) > 2 else ""
            row_data["route"] = cols[3].get_text(strip=True) if len(cols) > 3 else ""
            row_data["dosage_form"] = cols[4].get_text(strip=True) if len(cols) > 4 else ""
            row_data["rld_rs_number"] = cols[5].get_text(strip=True) if len(cols) > 5 else ""
            row_data["date_recommended"] = cols[6].get_text(strip=True) if len(cols) > 6 else ""

            # Normalize whitespaces
            for key in row_data:
                if isinstance(row_data[key], str):
                    row_data[key] = " ".join(row_data[key].split())

            data.append(row_data)

        return data

    except Exception as e:
        print(f"Exception raised while scraping letter {letter}: {e}")
        return []

def save_metadata_to_csv(data, csv_file_path):
    """
    Saves the list of metadata dictionaries to a CSV file.
    """
    csv_headers = [
        "Active Ingredient (link to Specific Guidance)",
        "URL",
        "Type",
        "Route",
        "Dosage Form",
        "RLD or RS Number",
        "Date Recommended"
    ]

    try:
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(csv_headers)
            
            for row in data:
                writer.writerow([
                    row["active_ingredient"],
                    row["pdf_url"],
                    row["type"],
                    row["route"],
                    row["dosage_form"],
                    row["rld_rs_number"],
                    row["date_recommended"]
                ])
        return True
    except Exception as e:
        print(f"Error saving to CSV {csv_file_path}: {e}")
        return False

def sync_all():
    """
    Main function to sync all FDA PSG metadata.
    """
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_dir_name = os.getenv("CSV_STORAGE_DIR", "csv")
    csv_folder = os.path.join(workspace_dir, csv_dir_name)
    
    print(f"Iniciando descarga y sincronización de metadatos FDA PSG en: {csv_folder}")
    
    total_records = 0
    for letter in string.ascii_uppercase:
        print(f"Procesando letra '{letter}'...", end="", flush=True)
        letter_data = get_fda_psg_metadata(letter)
        
        if letter_data:
            csv_path = os.path.join(csv_folder, f"{letter}.csv")
            if save_metadata_to_csv(letter_data, csv_path):
                print(f" Completado. {len(letter_data)} registros guardados.")
                total_records += len(letter_data)
            else:
                print(" Error al guardar el CSV.")
        else:
            print(" Sin datos o error en la petición.")

    print(f"Proceso finalizado. Total de registros sincronizados: {total_records}")

if __name__ == "__main__":
    sync_all()

