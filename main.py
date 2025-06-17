from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import os, zipfile, uuid, shutil, traceback
from handler import upscale_images
from fastapi.concurrency import run_in_threadpool


def _cleanup(paths):
    """Remove temporary files and directories."""
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
        # Imprime la traza completa en los logs del Pod
        tb = traceback.format_exc()
        print("❗️ Exception in /process/:\n", tb)
        # Devuelve un 500 con el mensaje de error
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if should_cleanup:
            _cleanup([zip_in, in_dir, out_dir, zip_out])
