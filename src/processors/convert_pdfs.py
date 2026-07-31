import os
import glob
import pdfplumber
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

# Obtener configuraciones de .env o usar valores por defecto
PDF_STORAGE_DIR = os.getenv("PDF_STORAGE_DIR", "data/pdf")
MARKDOWN_STORAGE_DIR = os.getenv("MARKDOWN_STORAGE_DIR", "data/markdown")

def table_to_markdown(table_data):
    """
    Converts raw table data (list of lists) into a Markdown table.
    """
    if not table_data or not any(table_data):
        return ""
    
    # Filter out empty rows or clean cells
    cleaned_rows = []
    for row in table_data:
        # Replace None with empty string and clean newlines
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                # Clean multiple spaces and newlines within cells to keep table format
                cleaned_cell = " ".join(cell.split())
                cleaned_row.append(cleaned_cell)
        
        # Keep row if it has at least some content
        if any(cleaned_row):
            cleaned_rows.append(cleaned_row)
            
    if not cleaned_rows:
        return ""
        
    # Generate Markdown Table
    headers = cleaned_rows[0]
    md_lines = []
    
    # Header row
    md_lines.append("| " + " | ".join(headers) + " |")
    # Separator row
    md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    # Data rows
    for row in cleaned_rows[1:]:
        # Adjust length if some row has fewer/more elements
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))
        elif len(row) > len(headers):
            row = row[:len(headers)]
        md_lines.append("| " + " | ".join(row) + " |")
        
    return "\n" + "\n".join(md_lines) + "\n"

def convert_pdf_to_markdown(pdf_path, md_path):
    """
    Extracts text and tables from a PDF using pdfplumber and writes them to a Markdown file.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            markdown_content = []
            
            for page_idx, page in enumerate(pdf.pages):
                # 1. Extract tables and their bounding boxes (bboxes)
                tables = page.find_tables()
                table_bboxes = [t.bbox for t in tables]
                extracted_tables_data = [t.extract() for t in tables]
                
                # We want to extract text but ignore areas occupied by tables to avoid duplication
                # Custom text extraction filter: exclude characters inside table bboxes
                def not_in_table(obj):
                    # Check if character is inside any table bbox (x0, top, x1, bottom)
                    if obj.get("object_type") == "char":
                        x0, top, x1, bottom = obj["x0"], obj["top"], obj["x1"], obj["bottom"]
                        for tx0, ttop, tx1, tbottom in table_bboxes:
                            # If character overlaps significantly with table
                            if (x0 >= tx0 - 1 and x1 <= tx1 + 1 and 
                                top >= ttop - 1 and bottom <= tbottom + 1):
                                return False
                    return True

                # Get text outside tables
                page_text_outside_tables = page.filter(not_in_table).extract_text(layout=False) or ""
                
                # Split text into paragraphs/lines
                lines = page_text_outside_tables.split("\n")
                cleaned_lines = []
                for line in lines:
                    line_strip = line.strip()
                    if line_strip:
                        # Simple rule to identify headings
                        if (line_strip.isupper() and len(line_strip) < 100) or line_strip.startswith("Recommended Studies"):
                            cleaned_lines.append(f"\n### {line_strip}\n")
                        else:
                            cleaned_lines.append(line_strip)
                
                page_text = "\n".join(cleaned_lines)
                markdown_content.append(f"## Página {page_idx + 1}\n")
                markdown_content.append(page_text)
                
                # Append extracted tables at the end of the page or in order
                if extracted_tables_data:
                    markdown_content.append("\n#### Tablas Extraídas:")
                    for table_data in extracted_tables_data:
                        md_table = table_to_markdown(table_data)
                        if md_table:
                            markdown_content.append(md_table)
                            
                markdown_content.append("\n---\n")
                
            # Write to Markdown file
            os.makedirs(os.path.dirname(md_path), exist_ok=True)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(markdown_content))
            return True
            
    except Exception as e:
        print(f"Error al procesar PDF {pdf_path}: {e}")
        return False

def main():
    workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Resolver rutas
    pdf_folder = os.path.join(workspace_dir, PDF_STORAGE_DIR) if not os.path.isabs(PDF_STORAGE_DIR) else PDF_STORAGE_DIR
    md_folder = os.path.join(workspace_dir, MARKDOWN_STORAGE_DIR) if not os.path.isabs(MARKDOWN_STORAGE_DIR) else MARKDOWN_STORAGE_DIR
    
    os.makedirs(md_folder, exist_ok=True)
    
    print(f"Buscando archivos PDF en: {pdf_folder}")
    pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    
    if not pdf_files:
        print("No se encontraron archivos PDF para convertir.")
        return
        
    total_pdfs = len(pdf_files)
    print(f"Se encontraron {total_pdfs} archivos PDF para convertir a Markdown.")
    
    converted_count = 0
    failed_count = 0
    skipped_count = 0
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        md_filename = filename.replace(".pdf", ".md")
        md_path = os.path.join(md_folder, md_filename)
        
        # Omitir si el MD ya existe y es más nuevo que el PDF (caché)
        if os.path.exists(md_path) and os.path.getmtime(md_path) > os.path.getmtime(pdf_path):
            skipped_count += 1
            print(f"\rProgreso: {idx}/{total_pdfs} | Omitido (ya convertido): {md_filename}", end="", flush=True)
            continue
            
        print(f"\rProgreso: {idx}/{total_pdfs} | Convirtiendo: {filename}...", end="", flush=True)
        
        success = convert_pdf_to_markdown(pdf_path, md_path)
        if success:
            converted_count += 1
        else:
            failed_count += 1
            
    print("\n\n--- Resumen del Proceso de Conversión ---")
    print(f"Total PDFs encontrados: {total_pdfs}")
    print(f"Convertidos con éxito: {converted_count}")
    print(f"Omitidos (ya al día): {skipped_count}")
    print(f"Errores: {failed_count}")

if __name__ == "__main__":
    main()
