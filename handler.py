import os
import torch
import cv2
from pathlib import Path
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

def upscale_images(input_folder, output_folder, model_path):
    # Validar existencia del modelo
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"❌ Modelo no encontrado en {model_path}")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Definir la arquitectura RRDBNet para x4
    model = RRDBNet(
        num_in_ch=3, num_out_ch=3,
        num_feat=64, num_block=23,
        num_grow_ch=32, scale=4
    )

    # Crear el objeto RealESRGANer
    upscaler = RealESRGANer(
        device=device,
        model=model,
        scale=4,
        model_path=model_path,
        half=False   # usa FP32 para mayor compatibilidad
    )

    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Procesar cada imagen
    for img_path in input_folder.rglob("*.[jp][pn]g"):
        print(f"[INFO] Procesando imagen: {img_path}")
        relative = img_path.relative_to(input_folder)
        output_path = output_folder / relative

        # Evitar reprocesar
        if output_path.exists():
            print(f"[SKIP] Ya existe: {output_path}")
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"[WARN] No se pudo leer {img_path}")
            continue

        # Upscale
        sr_img, _ = upscaler.enhance(img, outscale=4)
        cv2.imwrite(str(output_path), sr_img)
        print(f"[INFO] Guardado: {output_path}")

    total = len(list(input_folder.rglob("*.[jp][pn]g")))
    print(f"[INFO] ✅ Completado: {total} imágenes procesadas.")