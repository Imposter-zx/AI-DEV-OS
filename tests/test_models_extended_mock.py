from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import ai_dev_os.models
from ai_dev_os.models import FORCE_MOCK, ModelConfig, UnslothTrainer, inference, train_model


@pytest.fixture(autouse=True)
def enable_mock():
    ai_dev_os.models.FORCE_MOCK = True
    yield
    ai_dev_os.models.FORCE_MOCK = False


@pytest.mark.asyncio
async def test_unsloth_save_checkpoint_mock(tmp_path):
    config = ModelConfig(model_name="test", task="train")
    trainer = UnslothTrainer(config)

    path = tmp_path / "checkpoint"
    success = await trainer.save_checkpoint(str(path))

    assert success is True
    assert (path / "config.json").exists()


@pytest.mark.asyncio
async def test_convenience_functions_mock():
    # train_model convenience
    with patch("ai_dev_os.models.ModelManager.train_model") as mock_train:
        mock_train.return_value = (True, {"loss": 0.1})
        success, metrics = await train_model("model", "dataset")
        assert success is True
        assert metrics["loss"] == 0.1

    # inference convenience
    with patch("ai_dev_os.models.BitNetInference.infer") as mock_infer:
        mock_infer.return_value = (True, "Response")
        success, response = await inference("path", "prompt")
        assert success is True
        assert response == "Response"
