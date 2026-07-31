import os
import sys
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

# Definir la ruta base del proyecto
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Resolver ruta del archivo de log desde .env (ruta absoluta o relativa)
log_relative_path = os.getenv("PIPELINE_LOG_FILE", "data/logs/pipeline.log")
if os.path.isabs(log_relative_path):
    log_file_path = log_relative_path
else:
    log_file_path = os.path.join(workspace_dir, log_relative_path)

# Asegurar que la carpeta contenedora del log exista
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logger = logging.getLogger("PipelineLogger")
logger.setLevel(logging.INFO)

# Formateador de logs con marca de tiempo
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Manejador rotativo: 5MB por archivo (5 * 1024 * 1024 bytes) y un máximo de 5 archivos históricos
rotating_handler = RotatingFileHandler(
    log_file_path,
    maxBytes=5 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
rotating_handler.setFormatter(formatter)
logger.addHandler(rotating_handler)

def run_script(script_path):
    """
    Runs a python script as a subprocess, streams output to terminal in real-time,
    and saves all outputs to the rotating log file.
    """
    header_msg = f"Iniciando ejecución de: {script_path}"
    print(f"\n==================================================")
    print(f" {header_msg}")
    print(f"==================================================")
    logger.info(f"=== {header_msg.upper()} ===")
    
    full_path = os.path.join(workspace_dir, script_path)
    
    # Run the script using the same Python interpreter and capture stdout & stderr
    process = subprocess.Popen(
        [sys.executable, full_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=workspace_dir
    )
    
    # Read the output line by line as it is generated
    for line in process.stdout:
        # Print to terminal in real time
        print(line, end="")
        # Save to rotating log file (strip whitespace and carriage return)
        clean_line = line.rstrip('\r\n')
        if clean_line:
            logger.info(clean_line)
            
    process.wait()
    
    if process.returncode != 0:
        error_msg = f"El script {script_path} falló con código de salida: {process.returncode}"
        print(f"\n[ERROR] {error_msg}")
        logger.error(error_msg)
        return False
    
    success_msg = f"{script_path} completado con éxito."
    print(f"[OK] {success_msg}")
    logger.info(f"=== {success_msg.upper()} ===\n")
    return True

def main():
    start_msg = "INICIANDO PIPELINE COMPLETO DE SINCRONIZACIÓN Y ACTUALIZACIÓN"
    print(start_msg)
    logger.info(f"==================== {start_msg} ====================")
    
    # Secuencia de ejecución del Pipeline
    pipeline_steps = [
        "src/scrapers/sync_metadata.py",  # Fase 0: Descarga/sincroniza metadatos
        "src/scrapers/download_pdfs.py",  # Fase 1: Descarga nuevos PDFs (omitirá existentes)
        "src/processors/convert_pdfs.py", # Fase 2: Convierte PDFs nuevos a MD (omitirá existentes)
        "src/processors/populate_db.py"    # Fase 3: Sincroniza BD y genera embeddings (omitirá existentes)
    ]
    
    for step in pipeline_steps:
        success = run_script(step)
        if not success:
            abort_msg = "PIPELINE ABORTADO debido a un error en el proceso."
            print(f"\n[PIPELINE ABORTADO] Se detectó un error en uno de los pasos.")
            logger.critical(abort_msg)
            sys.exit(1)
            
    finish_msg = "PIPELINE DE SINCRONIZACIÓN COMPLETADO CON ÉXITO"
    print(f"\n==================================================")
    print(f" {finish_msg}")
    print(f"==================================================")
    logger.info(f"==================== {finish_msg} ====================\n")

if __name__ == "__main__":
    main()
