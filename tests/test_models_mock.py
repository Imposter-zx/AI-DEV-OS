import pytest

import ai_dev_os.models
from ai_dev_os.models import (
    BitNetInference,
    ModelConfig,
    ModelManager,
    UnslothTrainer,
)


@pytest.fixture(autouse=True)
def enable_mock():
    # Set the global mock flag
    ai_dev_os.models.FORCE_MOCK = True
    yield
    ai_dev_os.models.FORCE_MOCK = False


@pytest.mark.asyncio
async def test_unsloth_trainer_mock():
    config = ModelConfig(model_name="test-model", task="train")
    trainer = UnslothTrainer(config)

    success, metrics = await trainer.train()

    assert success is True
    assert metrics["final_loss"] == 0.5
    assert len(trainer.training_logs) == 1


@pytest.mark.asyncio
async def test_bitnet_inference_mock():
    engine = BitNetInference("test-path")
    success, response = await engine.infer("Test prompt")

    assert success is True
    assert "MOCK INF" in response


@pytest.mark.asyncio
async def test_model_manager_integration_mock():
    manager = ModelManager()
    config = ModelConfig(model_name="test-model", task="train")

    # Train
    success, metrics = await manager.train_model(config)
    assert success is True

    # Inference (manual load for mock test)
    await manager.load_inference_engine("test-path", "test-model")
    success, response = await manager.infer("test-model", "Test prompt")

    assert success is True
    assert "MOCK INF" in response
