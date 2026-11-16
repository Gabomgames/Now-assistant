"""Experimental GPU LoRA preparation. Dry-run is offline and never imports training libraries."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

try:
    from .validate_dataset import ROOT, check_file, check_eval_file, check_separation
except ImportError:
    from validate_dataset import ROOT, check_file, check_eval_file, check_separation

MODELS = ("Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen3-0.6B")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODELS, default=MODELS[0])
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/now_seed.jsonl")
    parser.add_argument("--validation-dataset", type=Path)
    parser.add_argument("--eval-cases", type=Path, default=ROOT / "data/eval_cases.jsonl")
    parser.add_argument("--provenance", type=Path, default=ROOT / "data/PROVENANCE.json")
    parser.add_argument("--output", type=Path, default=ROOT / "runs/now-lora-experiment")
    parser.add_argument("--allow-model-download", action="store_true",
                        help="allow normal model download only in an environment whose network policy permits it")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def build_plan(args):
    count, errors = check_file(args.dataset)
    evaluation_count, evaluation_errors = check_eval_file(args.eval_cases)
    errors += ["evaluation: " + error for error in evaluation_errors]
    blockers = []
    validation_count = 0
    if args.validation_dataset is not None:
        validation_count, validation_errors = check_file(args.validation_dataset)
        errors += ["validation: " + error for error in validation_errors]
    else:
        blockers.append("a separate reviewed validation dataset is required")
    errors += check_separation(args.dataset, args.eval_cases, args.validation_dataset)
    if count < 100:
        blockers.append("pilot dataset has fewer than 100 examples; expand and review it first (100 is not a quality guarantee)")
    try:
        provenance = json.loads(args.provenance.read_text(encoding="utf-8"))
        if not isinstance(provenance, dict):
            raise ValueError("provenance must be an object")
        if provenance.get("dataset_sha256") != hashlib.sha256(args.dataset.read_bytes()).hexdigest():
            errors.append("provenance checksum does not match this training dataset")
        if provenance.get("approved_for_training") is not True or not all(
            isinstance(provenance.get(field), str) and provenance[field].strip()
            for field in ("license", "rights_basis", "reviewed_by", "reviewed_at")
        ):
            blockers.append("dataset rights/provenance review has not approved this exact dataset")
    except (OSError, UnicodeError, ValueError) as error:
        errors.append("cannot validate provenance: " + type(error).__name__)
    if args.output.exists():
        blockers.append("output directory already exists; choose a new path to preserve previous work")
    return {
        "mode": "DRY_RUN" if args.dry_run else "GPU_TRAINING_REQUEST",
        "model": args.model,
        "train_records": count,
        "validation_records": validation_count,
        "held_out_cases": evaluation_count,
        "validation_dataset": str(args.validation_dataset) if args.validation_dataset else None,
        "dataset": str(args.dataset),
        "output": str(args.output),
        "local_files_only": not args.allow_model_download,
        "errors": errors,
        "training_blockers": blockers,
        "training_executed": False,
        "gpu_dependencies_checked": False,
        "note": "No model is loaded by this planning step. Real training additionally requires reviewed model licensing, a baseline evaluation and a compatible CUDA environment.",
    }


def main(argv=None):
    args = parse_args(argv)
    plan = build_plan(args)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if plan["errors"]:
        return 1
    if args.dry_run:
        return 0
    if plan["training_blockers"]:
        print("TRAINING NOT STARTED: resolve every recorded blocker first.")
        return 2
    try:
        import torch
        from datasets import load_dataset
        from peft import LoraConfig
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from trl import SFTConfig, SFTTrainer
    except ImportError as error:
        print("TRAINING NOT STARTED: optional GPU dependencies are missing:", type(error).__name__)
        return 2
    if not torch.cuda.is_available():
        print("TRAINING NOT STARTED: a compatible CUDA GPU is required; CPU training is not enabled.")
        return 2

    # This branch is experimental until exercised on a licensed, approved corpus and CUDA runner.
    local_only = not args.allow_model_download
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=local_only, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, local_files_only=local_only, trust_remote_code=False, torch_dtype=torch.float16,
    )
    datasets = load_dataset("json", data_files={"train": str(args.dataset), "validation": str(args.validation_dataset)})
    persona = (ROOT / "prompts/now-casual-v1.txt").read_text(encoding="utf-8").strip()

    def add_system(row):
        return {"prompt": [{"role": "system", "content": persona}, *row["prompt"]], "completion": row["completion"]}

    datasets = datasets.map(add_system)
    args.output.mkdir(parents=True, exist_ok=False)
    config = SFTConfig(
        output_dir=str(args.output), per_device_train_batch_size=1, gradient_accumulation_steps=8,
        num_train_epochs=2, learning_rate=1e-4, logging_steps=10, max_length=512,
        report_to="none", completion_only_loss=True, save_strategy="epoch", eval_strategy="epoch",
        fp16=True, seed=42, data_seed=42,
    )
    lora = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
                      task_type="CAUSAL_LM", target_modules="all-linear")
    trainer = SFTTrainer(model=model, processing_class=tokenizer, args=config,
                         train_dataset=datasets["train"], eval_dataset=datasets["validation"], peft_config=lora)
    trainer.train()
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    plan.update(training_executed=True, completed_at_utc=datetime.now(timezone.utc).isoformat())
    (args.output / "training-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Adapter saved. Independent evaluation, export and runtime validation are still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
