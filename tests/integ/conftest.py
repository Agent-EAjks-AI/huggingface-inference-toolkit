import docker
import pytest
import random
import logging
from tests.integ.config import task2model
import tenacity
import time
import tempfile
from huggingface_inference_toolkit.utils import (
    _is_gpu_available,
    _load_repository_from_hf
)
from transformers.testing_utils import (
    slow,
    _run_slow_tests
)
import uuid
import socket

IS_GPU = _run_slow_tests
DEVICE = "gpu" if IS_GPU else "cpu"

@tenacity.retry(
    retry = tenacity.retry_if_exception(docker.errors.APIError),
    stop = tenacity.stop_after_attempt(10)
)
@pytest.fixture(scope = "function")
def remote_container(
    device,
    task,
    framework
):
    time.sleep(random.randint(1, 5))
    #client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    client = docker.from_env()
    container_name = f"integration-test-{framework}-{task}-{device}"
    container_image = f"integration-test-{framework}:{device}"
    port = random.randint(5000, 9000)
    model = task2model[task][framework]

    #check if port is already open
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while sock.connect_ex(("localhost", port)) == 0:
        logging.debug(f"Port {port} is already being used; getting a new one...")
        port = random.randint(5000, 9000)

    logging.debug(f"Image: {container_image}")
    logging.debug(f"Port: {port}")

    device_request = [
        docker.types.DeviceRequest(
            count=-1,
            capabilities=[["gpu"]])
    ] if device == "gpu" else []

    yield client.containers.run(
        image = container_image,
        name=container_name,
        ports={"5000": port},
        environment={
            "HF_MODEL_ID": model,
            "HF_TASK": task,
            "CUDA_LAUNCH_BLOCKING": 1
        },
        detach=True,
        # GPU
        device_requests=device_request,
    ), port

    #Teardown
    previous = client.containers.get(container_name)
    previous.stop()
    previous.remove()


@tenacity.retry(
    stop = tenacity.stop_after_attempt(10),
    reraise = True
)
@pytest.fixture(scope = "function")
def local_container(
    device,
    task,
    repository_id,
    framework
):
    try:
        time.sleep(random.randint(1, 5))
        id = uuid.uuid4()
        if not (task == "custom"):
            model = task2model[task][framework]
            id = task
        else:
            model = repository_id

        logging.info(f"Starting container with model: {model}")

        if not model:
            message = f"No model supported for {framework}"
            logging.error(message)
            raise ValueError(message)
        
        logging.info(f"Starting container with Model = {model}")
        client = docker.from_env()
        container_name = f"integration-test-{framework}-{id}-{device}"
        container_image = f"integration-test-{framework}:{device}"

        port = random.randint(5000, 9000)

        #check if port is already open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while sock.connect_ex(("localhost", port)) == 0:
            logging.debug(f"Port {port} is already being used; getting a new one...")
            port = random.randint(5000, 9000)

        logging.debug(f"Image: {container_image}")
        logging.debug(f"Port: {port}")

        device_request = [
            docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])
        ] if device == "gpu" else []

        object_id = model.replace("/", "--")
        model_dir = f"/mnt/hf_cache/hub/{object_id}"

        storage_dir = _load_repository_from_hf(
            repository_id = model,
            target_dir = model_dir,
            framework = framework
        )

        yield client.containers.run(
            container_image,
            name=container_name,
            ports={"5000": port},
            environment={
                "HF_MODEL_DIR": "/opt/huggingface/model",
                "HF_TASK": task
            },
            volumes = {
                model_dir: {
                    "bind": "/opt/huggingface/model",
                    "mode": "ro"
                }
            },
            detach=True,
            # GPU
            device_requests=device_request,
        ), port

        #Teardown
        previous = client.containers.get(container_name)
        previous.stop()
        previous.remove()
    except Exception as exception:
        logging.error(f"Error starting container: {str(exception)}")
        raise exception

