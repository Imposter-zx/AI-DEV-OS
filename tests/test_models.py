import pytest
from ai_dev_os.models import ModelConfig, UnslothTrainer, QuantizationType

@pytest.mark.asyncio
async def test_model_config():
    config = ModelConfig(model_name="test-model", task="train", quantization=QuantizationType.BITNET_1BIT)
    assert config.model_name == "test-model"
    assert config.quantization == QuantizationType.BITNET_1BIT

@pytest.mark.asyncio
async def test_unsloth_trainer_mock(monkeypatch):
    config = ModelConfig(model_name="test-model", task="train")
    trainer = UnslothTrainer(config)
    
    success, metrics = await trainer.train()
    assert success is True
    assert "final_loss" in metrics
    assert metrics["vram_reduction_percent"] > 0
