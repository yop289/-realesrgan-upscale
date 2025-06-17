FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /workspace

COPY requirements.txt .
RUN apt-get update && apt-get install -y git zip unzip ffmpeg libgl1 && \
    pip install --no-cache-dir -r requirements.txt

COPY RealESRGAN_x4plus.pth /workspace/model/RealESRGAN_x4plus.pth
COPY handler.py .

CMD ["python", "handler.py"]