# Kenya SAM-Augmented Semantic Segmentation using U-Net

This directory contains code to perform experiments on the Source Cooperative dataset, available [at this link](https://source.coop/repositories/ksa/kenol-section/description), using Segment Anything Model (SAM) and a U-Net architecture.

## Instructions to run the code using Docker:

**Step 1-** Change directory to an empty folder in your machine and clone the repo.
```
$ cd /to_empty/dir/on_host/

$ git clone  git@github.com:ClarkCGA/multi-temporal-crop-classification-baseline.git

$ cd path/to/cloned directory/
```

**Step 2-** Make sure the Docker daemon is running and build the Docker image as following:
```
$ docker build -t <image_name>:<tag> .
```
Example:
```
$ docker build -t kenya_sam:1.0 .
```

**step 3-** Run the Docker image as a container from within the cloned folder:
```
$ docker run --gpus all -it -p 8888:8888 -v <path/to/the/cloned-repo/on-host>:/app/ <image_name>:<tag>
```
or alternately use docker compose:

```
docker compose up
```

Either command will start a container based on the specified Docker image and starts a JupyterLab session. Type `localhost:8888` in your browser and copy the provided token from the terminal to open the JupyterLab.

**step 4-** Run the pipeline:

Open the jupyter notebook located at `notebooks/main.ipynb`.

Modify the "default_config.yaml" or create your own config file and run the cells as explained in the notebook.


