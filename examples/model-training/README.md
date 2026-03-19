# Model Fine-tuning Example

This example demonstrates how to use `UnslothTrainer` to fine-tune a Llama-3 model and quantize it to BitNet format.

## Usage

1. Prepare your dataset in `data/custom.csv`.
2. Run the training script:
```bash
python train.py --dataset ./data/custom.csv --output ./models/custom.gguf
```

## Features
- 2x speedup via Unsloth.
- 1-bit quantization for BitNet inference.
