import tempfile
from tests.integ.helpers import verify_task
from tests.integ.config import (
    task2input,
    task2model,
    task2output,
    task2validation
)
from transformers.testing_utils import (
    require_torch,
    slow,
    _run_slow_tests
)
import pytest
import tenacity
import docker

class TestTensorflowRemote:

    @tenacity.retry(
        retry = tenacity.retry_if_exception(docker.errors.APIError),
        stop = tenacity.stop_after_attempt(3)
    )
    @pytest.mark.parametrize(
        "device",
        ["gpu", "cpu"]
    )
    @pytest.mark.parametrize(
        "task",
        [
            "text-classification",
            "zero-shot-classification",
            "ner",
            "question-answering",
            "fill-mask",
            "summarization",
            "translation_xx_to_yy",
            "text2text-generation",
            "text-generation",
            "feature-extraction",
            "image-classification",
            "conversational",
        ]
    )
    @pytest.mark.parametrize(
        "framework",
        ["tensorflow"]
    )
    @pytest.mark.usefixtures('remote_container')
    def test_inference_remote(self, remote_container, task, framework, device):

        verify_task(
            task = task,
            port = remote_container[1],
            framework = framework
        )
