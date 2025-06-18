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

    model = RRDBNet(
        num_in_ch=3, num_out_ch=3,
        num_feat=64, num_block=23,
        num_grow_ch=32, scale=4
    )

    upscaler = RealESRGANer(
        device=device,
        model=model,
        scale=4,
        model_path=model_path,
        half=False,
        tile=512,     # <-- CLAVE para OOM
        tile_pad=10
    )

    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    patterns = ['*.jpg', '*.jpeg', '*.png']
    img_paths = []
    for pattern in patterns:
        img_paths.extend(input_folder.rglob(pattern))

    for img_path in img_paths:
        print(f"[INFO] Procesando imagen: {img_path}")
        relative = img_path.relative_to(input_folder)
        output_path = output_folder / relative

        if output_path.exists():
            print(f"[SKIP] Ya existe: {output_path}")
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"[WARN] No se pudo leer {img_path}")
            continue

        sr_img, _ = upscaler.enhance(img, outscale=4)
        cv2.imwrite(str(output_path), sr_img)
        print(f"[INFO] Guardado: {output_path}")
        torch.cuda.empty_cache()   # <-- Esto libera memoria GPU entre imágenes

    total = len(img_paths)
    print(f"[INFO] ✅ Completado: {total} imágenes procesadas.")