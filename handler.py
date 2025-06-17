import os
from realesrgan import RealESRGAN
import torch
import cv2
from pathlib import Path

def upscale_images(input_folder, output_folder, model_path):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = RealESRGAN(device, scale=4)
    model.load_weights(model_path)

    input_folder = Path(input_folder)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    for img_path in input_folder.rglob("*.[jp][pn]g"):
        relative = img_path.relative_to(input_folder)
        output_path = output_folder / relative
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"Error cargando {img_path}")
            continue

        sr_img = model.predict(img)
        cv2.imwrite(str(output_path), sr_img)
        print(f"✅ {img_path} → {output_path}")

if __name__ == "__main__":
    upscale_images("input", "output", "model/RealESRGAN_x4plus.pth")