import os
import tempfile
from PIL import Image
from transformers.testing_utils import require_torch, slow


from huggingface_inference_toolkit.diffusers_utils import get_diffusers_pipeline, IEAutoPipelineForText2Image
from huggingface_inference_toolkit.utils import _load_repository_from_hf, get_pipeline


@require_torch
def test_get_diffusers_pipeline():
    with tempfile.TemporaryDirectory() as tmpdirname:
        storage_dir = _load_repository_from_hf(
            "hf-internal-testing/tiny-stable-diffusion-torch", tmpdirname, framework="pytorch"
        )
        pipe = get_pipeline("text-to-image", storage_dir.as_posix())
        assert isinstance(pipe, IEAutoPipelineForText2Image)


@slow
@require_torch
def test_pipe_on_gpu():
    with tempfile.TemporaryDirectory() as tmpdirname:
        storage_dir = _load_repository_from_hf(
            "hf-internal-testing/tiny-stable-diffusion-torch", tmpdirname, framework="pytorch"
        )
        pipe = get_pipeline("text-to-image", storage_dir.as_posix())
        assert pipe.device.type == "cuda"


@require_torch
def test_text_to_image_task():
    with tempfile.TemporaryDirectory() as tmpdirname:
        storage_dir = _load_repository_from_hf(
            "hf-internal-testing/tiny-stable-diffusion-torch", tmpdirname, framework="pytorch"
        )
        pipe = get_pipeline("text-to-image", storage_dir.as_posix())
        res = pipe("Lets create an embedding")
        assert isinstance(res, Image.Image)
