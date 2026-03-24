import pytest

from ai_dev_os.models import ModelConfig, QuantizationType, UnslothTrainer


@pytest.mark.asyncio
async def test_model_config():
    config = ModelConfig(
        model_name="test-model", task="train", quantization=QuantizationType.BITNET_1BIT
    )
    assert config.model_name == "test-model"
    assert config.quantization == QuantizationType.BITNET_1BIT


@pytest.mark.asyncio
async def test_unsloth_trainer_mock(monkeypatch):
    import unittest.mock
    config = ModelConfig(model_name="test-model", task="train")
    trainer = UnslothTrainer(config)

    # Since the real implementation requires a real CUDA GPU and unsloth, 
    # we explicitly mock it here for CI testing.
    with unittest.mock.patch.object(UnslothTrainer, 'setup', return_value=True):
        with unittest.mock.patch.object(
            UnslothTrainer, 'train', 
            return_value=(True, {"final_loss": 1.2, "vram_reduction_percent": 70.0})
        ):
            success, metrics = await trainer.train()
            assert success is True
            assert "final_loss" in metrics
            assert metrics["vram_reduction_percent"] > 0
