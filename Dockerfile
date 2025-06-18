FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

WORKDIR /workspace

# 1) Copiamos explícitamente todos los archivos Python y el requirements
COPY . .

# 2) (Opcional) Si tienes otros módulos .py, inclúyelos también:
# COPY utils.py other_module.py ./

# 3) Instalamos dependencias de sistema
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3-pip zip unzip wget git libgl1-mesa-glx libglib2.0-0 tzdata \
 && rm -rf /var/lib/apt/lists/*

# 4) Instalamos PyTorch con soporte CUDA 11.8 (sm_86) y luego el resto
RUN pip3 install --upgrade pip \
 && pip3 install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118 \
 && pip3 install -r requirements.txt

# 5) Descarga el modelo Real-ESRGAN
RUN mkdir -p weights \
 && wget -O weights/RealESRGAN_x4plus.pth \
      https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/workspace"]