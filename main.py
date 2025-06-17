from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os, zipfile, uuid, shutil, traceback
from handler import upscale_images

app = FastAPI()

@app.post("/process/")
async def process_zip(file: UploadFile = File(...)):
    job_id = uuid.uuid4().hex
    base_dir = "/workspace"
    zip_in = os.path.join(base_dir, f"input_{job_id}.zip")
    in_dir  = os.path.join(base_dir, f"input_{job_id}")
    out_dir = os.path.join(base_dir, f"output_{job_id}")
    zip_out = os.path.join(base_dir, f"result_{job_id}.zip")

    try:
        # 1. Guardar .zip subido
        with open(zip_in, "wb") as f:
            f.write(await file.read())
        # 2. Descomprimir
        os.makedirs(in_dir, exist_ok=True)
        with zipfile.ZipFile(zip_in, 'r') as zf:
            zf.extractall(in_dir)
        # 3. Upscale
        os.makedirs(out_dir, exist_ok=True)
        model_path = "weights/RealESRGAN_x4plus.pth"
        upscale_images(in_dir, out_dir, model_path)
        # 4. Comprimir resultado
        shutil.make_archive(zip_out.replace('.zip',''), 'zip', out_dir)
        # 5. Devolver con nombre dinámico
        orig = file.filename.rsplit(".",1)[0]
        return FileResponse(zip_out,
                            media_type="application/zip",
                            filename=f"{orig}_x4.zip")
    except Exception as e:
        # Imprime la traza completa en los logs del Pod
        tb = traceback.format_exc()
        print("❗️ Exception in /process/:\n", tb)
        # Devuelve un 500 con el mensaje de error
        raise HTTPException(status_code=500, detail=str(e))
