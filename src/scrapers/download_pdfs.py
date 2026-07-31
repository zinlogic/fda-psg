import os
import csv
import glob
import time
import requests
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

# Obtener configuraciones de .env o usar valores por defecto
CSV_STORAGE_DIR = os.getenv("CSV_STORAGE_DIR", "data/csv")
PDF_STORAGE_DIR = os.getenv("PDF_STORAGE_DIR", "data/pdf")
USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
DOWNLOAD_DELAY = float(os.getenv("DOWNLOAD_DELAY", "1.0"))  # Pausa de cortesía en segundos

def download_pdf(url, dest_path, headers):
    """
    Downloads a single PDF file from the URL to the destination path.
    """
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        else:
            print(f"\n[ERROR] Error al descargar {url}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"\n[ERROR] Excepción durante la descarga de {url}: {e}")
        return False

def main():
    # Obtener la ruta base del proyecto
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Resolver rutas absolutas
    csv_folder = os.path.join(workspace_dir, CSV_STORAGE_DIR) if not os.path.isabs(CSV_STORAGE_DIR) else CSV_STORAGE_DIR
    pdf_folder = os.path.join(workspace_dir, PDF_STORAGE_DIR) if not os.path.isabs(PDF_STORAGE_DIR) else PDF_STORAGE_DIR
    
    os.makedirs(pdf_folder, exist_ok=True)
    
    print(f"Buscando archivos CSV en: {csv_folder}")
    csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))
    
    if not csv_files:
        print("No se encontraron archivos CSV en el directorio configurado.")
        return

    # Recopilar todos los enlaces PDF únicos
    pdf_tasks = {}
    for csv_file in csv_files:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # El link puede estar en la columna 'URL' o 'Active Ingredient (link to Specific Guidance)'
                url = row.get("URL") or row.get("Active Ingredient (link to Specific Guidance)")
                
                # Validar que sea una URL de PDF
                if url and isinstance(url, str) and url.lower().endswith(".pdf"):
                    filename = os.path.basename(url)
                    if filename:
                        pdf_tasks[filename] = url

    total_pdfs = len(pdf_tasks)
    print(f"Se encontraron {total_pdfs} guías (PDFs únicos) para procesar.")
    
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    headers = {
        "User-Agent": USER_AGENT
    }
    
    for idx, (filename, url) in enumerate(pdf_tasks.items(), 1):
        dest_path = os.path.join(pdf_folder, filename)
        
        # Verificar si ya existe el PDF localmente (caché)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            skipped_count += 1
            # Imprimir progreso simplificado en la misma línea
            print(f"\rProgreso: {idx}/{total_pdfs} | Omitido (ya existe): {filename}", end="", flush=True)
            continue
        
        print(f"\rProgreso: {idx}/{total_pdfs} | Descargando: {filename}...", end="", flush=True)
        
        success = download_pdf(url, dest_path, headers)
        if success:
            downloaded_count += 1
            # Pausa de cortesía para no saturar el servidor de la FDA
            if DOWNLOAD_DELAY > 0:
                time.sleep(DOWNLOAD_DELAY)
        else:
            failed_count += 1
            
    print("\n\n--- Resumen del Proceso de Descarga ---")
    print(f"Total procesados: {total_pdfs}")
    print(f"Descargados nuevos: {downloaded_count}")
    print(f"Omitidos (ya descargados): {skipped_count}")
    print(f"Errores: {failed_count}")

if __name__ == "__main__":
    main()
