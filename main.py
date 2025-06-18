from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import os, zipfile, uuid, shutil, traceback
from handler import upscale_images
from fastapi.concurrency import run_in_threadpool
from pathlib import Path

def _cleanup(paths):
    for p in paths:
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            elif os.path.isfile(p):
                os.remove(p)
        except Exception as e:
            print(f"[WARN] cleanup failed for {p}: {e}")

app = FastAPI()

@app.post("/process/")
async def process_zip(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    job_id = uuid.uuid4().hex
    base_dir = "/workspace"
    zip_in = os.path.join(base_dir, f"input_{job_id}.zip")
    in_dir  = os.path.join(base_dir, f"input_{job_id}")
    out_dir = os.path.join(base_dir, f"output_{job_id}")
    zip_out = os.path.join(base_dir, f"result_{job_id}.zip")

    should_cleanup = True
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
        await run_in_threadpool(upscale_images, in_dir, out_dir, model_path)
        # 4. Comprimir resultado
        shutil.make_archive(zip_out.replace('.zip',''), 'zip', out_dir)
        # 5. Devolver con nombre dinámico
        orig = file.filename.rsplit(".", 1)[0]
        background_tasks.add_task(
            _cleanup, [zip_in, in_dir, out_dir, zip_out]
        )
        should_cleanup = False
        return FileResponse(
            zip_out,
            media_type="application/zip",
            filename=f"{orig}_x4.zip",
        )
    except Exception as e:
        tb = traceback.format_exc()
        print("❗️ Exception in /process/:\n", tb)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if should_cleanup:
            _cleanup([zip_in, in_dir, out_dir, zip_out])

# NUEVO ENDPOINT: Procesar imagen individual
@app.post("/process_image/")
async def process_image(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    job_id = uuid.uuid4().hex
    base_dir = "/workspace"
    input_dir  = os.path.join(base_dir, f"inimg_{job_id}")
    output_dir = os.path.join(base_dir, f"outimg_{job_id}")

    should_cleanup = True
    try:
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        # Guardar la imagen
        orig_name = Path(file.filename).stem
        ext = os.path.splitext(file.filename)[1].lower()
        input_img = os.path.join(input_dir, f"{orig_name}{ext}")
        with open(input_img, "wb") as f:
            f.write(await file.read())
        # Upscale
        model_path = "weights/RealESRGAN_x4plus.pth"
        await run_in_threadpool(upscale_images, input_dir, output_dir, model_path)
        # Encontrar imagen procesada (debería haber solo una)
        out_files = list(Path(output_dir).rglob("*"+ext))
        if not out_files:
            raise Exception("No se generó imagen de salida.")
        result_img = str(out_files[0])
        result_name = f"{orig_name}_x4{ext}"
        background_tasks.add_task(_cleanup, [input_dir, output_dir])
        should_cleanup = False
        return FileResponse(
            result_img,
            media_type="image/png" if ext in [".png"] else "image/jpeg",
            filename=result_name
        )
    except Exception as e:
        tb = traceback.format_exc()
        print("❗️ Exception in /process_image/:\n", tb)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if should_cleanup:
            _cleanup([input_dir, output_dir])