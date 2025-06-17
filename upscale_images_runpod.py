import os
import zipfile
import requests
import shutil
import time
from tqdm import tqdm
from dotenv import load_dotenv

# -------------------- CONFIG --------------------
load_dotenv()
RUNPOD_ENDPOINT = os.getenv("RUNPOD_ENDPOINT")  # e.g. https://tmrvqxx6i8p1qf-8000.proxy.runpod.net/process/

if not RUNPOD_ENDPOINT:
    raise ValueError("❌ Falta la variable RUNPOD_ENDPOINT en el .env")

BASE_DIR = os.getcwd()
HEADERS = {}  # Si necesitas auth, aquí puedes ponerla
# ------------------------------------------------

def log(msg):
    print(f"[INFO] {msg}")

def comprimir_carpeta(nombre):
    carpeta = os.path.join(BASE_DIR, nombre)
    zip_path = os.path.join(BASE_DIR, f"{nombre}.zip")
    if not os.path.exists(zip_path):
        log(f"🗜️  Comprimiendo {nombre}...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(carpeta):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, carpeta)
                    zipf.write(filepath, arcname=os.path.join(nombre, arcname))
        shutil.rmtree(carpeta)
        log(f"🧹 Carpeta {nombre} eliminada después de comprimir.")

def encontrar_zips():
    return [f for f in os.listdir(BASE_DIR) if f.endswith(".zip") and not f.endswith(".PROCESADO.zip")]

def enviar_a_runpod(zip_path):
    log(f"🚀 Subiendo {zip_path} a RunPod")
    with open(zip_path, "rb") as f:
        files = {"file": (os.path.basename(zip_path), f, "application/zip")}
        response = requests.post(RUNPOD_ENDPOINT, headers=HEADERS, files=files)
    if response.status_code != 200:
        raise Exception(f"❌ Error en RunPod: {response.status_code} - {response.text}")
    log("📥 Descargando archivo procesado...")
    output_path = zip_path.replace(".zip", "_x4.zip")
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path

def procesar():
    log("🔍 Buscando carpetas...")
    carpetas = [d for d in os.listdir(BASE_DIR) if os.path.isdir(d) and d.isdigit()]
    for carpeta in carpetas:
        comprimir_carpeta(carpeta)

    zips = encontrar_zips()
    if not zips:
        log("🟡 No hay ZIPs para procesar.")
        return

    for zip_name in zips:
        zip_path = os.path.join(BASE_DIR, zip_name)
        try:
            output_file = enviar_a_runpod(zip_path)
            log(f"✅ Procesado: {output_file}")
            nuevo_nombre = zip_path.replace(".zip", ".PROCESADO.zip")
            os.rename(zip_path, nuevo_nombre)
            log(f"♻️  Renombrado original: {zip_name} → {os.path.basename(nuevo_nombre)}")
        except Exception as e:
            log(f"❌ Error procesando {zip_name}: {e}")

if __name__ == "__main__":
    log("🧠 Iniciando procesamiento RunPod...")
    procesar()
