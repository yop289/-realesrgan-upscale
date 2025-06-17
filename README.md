# Real-ESRGAN Upscale Service

This repository contains a small FastAPI application to upscale images using [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN). The service expects a `.zip` file of images and returns another `.zip` with the images upscaled 4x.

## Building the Docker image

```bash
docker build -t realesrgan-upscale .
```

The provided `Dockerfile` installs PyTorch with CUDA support and downloads the pre-trained Real-ESRGAN model.

## Running the service

```bash
docker run --gpus all -p 8000:8000 realesrgan-upscale
```

The API will be available at `http://localhost:8000`. The single endpoint is `POST /process/`.

## Uploading a ZIP file

Send a `multipart/form-data` request with a `.zip` file containing images. The server will return a `.zip` with the upscaled results.

Example using `curl`:

```bash
curl -X POST \
     -F "file=@your_images.zip" \
     http://localhost:8000/process/ -o result.zip
```

The response file will contain all processed images suffixed with `_x4`.
