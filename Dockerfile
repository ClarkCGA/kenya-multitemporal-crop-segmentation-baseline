FROM python:3.10

# Install dependecies for GDAL
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev && \
    rm -rf /var/lib/apt/lists/*


# Install PyTorch with CUDA support and openCV
RUN pip install torch==2.0.0+cu117 torchvision==0.15.1+cu117 torchaudio==2.0.1 --index-url https://download.pytorch.org/whl/cu117
RUN pip install opencv-python-headless

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Expose the port for Jupyter Notebook
EXPOSE 8888

# Launch Jupyter Notebook when the container starts
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--ServerApp.token=''"]
