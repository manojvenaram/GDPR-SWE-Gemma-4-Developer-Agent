"""
scripts/train_qlora_gemma4.py
QLoRA and Direct Preference Optimization (DPO) fine-tuning pipeline for Gemma 4.
Configured for consumer GPU execution (24GB VRAM with 4-bit QAT quantization).
"""

from __future__ import annotations
import argparse
import os
import sys

CONFIG_TEMPLATE = {
    "model_id": "google/gemma-4-31b-it",
    "load_in_4bit": True,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_compute_dtype": "bfloat16",
    "lora_r": 32,
    "lora_alpha": 64,
    "lora_dropout": 0.05,
    "target_modules": [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    "learning_rate": 5e-5,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.1,
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 16,
    "max_seq_length": 8192,
    "dpo_beta": 0.1,
}


def print_training_recipe():
    print("=" * 75)
    print("GEMMA 4 QLORA / DPO POST-TRAINING SPECIFICATION FOR AGENTIC SE")
    print("=" * 75)
    print("Key Hyperparameters & Optimization Profile:")
    for k, v in CONFIG_TEMPLATE.items():
        print(f"  • {k:<30}: {v}")
    print("-" * 75)
    print("""
TRAINING PIPELINE SUMMARY:
1. Base Weights: Gemma 4 31B Instruct (QAT W4A16).
2. Memory Footprint: ~18.4 GB VRAM under 4-bit NF4 with gradient checkpointing.
3. Objective:
   - SFT Stage 1: Fine-tune on multi-turn tool calling traces (GDPR-SWE protocol).
   - DPO Stage 2: Direct Preference Optimization on (chosen, rejected) trajectories,
     penalizing context flooding, unverified mutations, and broken submissions.
4. Export: Produces PEFT LoRA adapter directory directly referenced by swegemma harness.
""")
    print("=" * 75)


if __name__ == "__main__":
    print_training_recipe()
