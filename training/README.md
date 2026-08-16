# CalTrack training pipeline

Infrastructure for collecting opted-in scanner feedback, validating it, splitting it, training a **candidate food classifier**, evaluating it, and requiring **human approval** before anything becomes production.

This does **not** replace the live vision model. Production food identification remains cloud vision (`gpt-4o-mini` by default) with calories from the CalTrack nutrition database until a candidate is approved.

Do not start real model training until `training/reports/latest.json` shows enough **validated corrected** examples.

## Commands

Run from the repository root (`CalTrack/`), with the `backend` virtualenv active if you use one.

```bash
python -m training.scripts.collect_feedback
python -m training.scripts.validate_dataset
python -m training.scripts.build_dataset
python -m training.scripts.train
python -m training.scripts.evaluate
python -m training.scripts.run_pipeline
```

Human-only promotion (never done by the default pipeline):

```bash
python -m training.scripts.promote --promote caltrack-food-v2
python -m training.scripts.promote --reject caltrack-food-v2
python -m training.scripts.promote --rollback caltrack-food-v1
```

`--rollback` restores a previous version (for example `caltrack-food-v3`) without retraining.

## Recommended operating loop

1. Collect feedback continuously (users who opt in on Settings).
2. Train periodically, not continuously.
3. Evaluate automatically.
4. Approve manually.
5. Deploy only an approved registry version.

Default quality gate (`training/quality_gate.json`):

- `minimum_accuracy = 0.90`
- `minimum_f1 = 0.90`
- `minimum_improvement = 0.01`
- `auto_promote = false`

Unedited predictions are stored as **confirmed**, not assumed-correct training labels. Dataset build uses **corrections** unless `include_confirmed_in_training` is enabled.

## Manual CLI

```bash
python -m training.scripts.run_pipeline
```

Inspect `training/reports/latest.json`. If `recommendation` is `DO_NOT_TRAIN` or `APPROVAL_REQUIRED`, do not promote.

## Windows Task Scheduler

1. Action: `python.exe`
2. Arguments: `-m training.scripts.run_pipeline`
3. Start in: `C:\Users\<you>\CalTrack`
4. Trigger: weekly (or after you know enough corrections exist)

Do not schedule promotion.

## GitHub Actions

Example workflow (evaluate only; no deploy):

```yaml
name: training-pipeline
on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * 1"
jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m training.scripts.run_pipeline
```

User images must not be committed. Keep `TRAINING_DATA_DIR` on private storage.

## Dataset layout

```
training/data/raw/images/   opted-in scans (generated filenames)
training/data/raw/feedback.jsonl
training/data/train/
training/data/validation/
training/data/test/         isolated evaluation set
training/data/dataset.jsonl
```

Splits are 70 / 15 / 15 by `analysis_id` (one photo cannot appear in both train and test). Seed `42`.

## Model strategy

`training/train.py` defines `ModelTrainer` (`prepare_dataset`, `train`, `evaluate`, `save_checkpoint`).

The first implementation is a **majority-class baseline**, not a from-scratch multimodal model. Transfer-learning a vision backbone can replace `MajorityClassTrainer` later. Target task: **food classification**. Portions stay in metadata for a future estimator. Calories stay in the nutrition database.

Training is skipped when validated training rows are below `min_samples_to_train` (default 50).

## Privacy

`allow_training_data_collection` defaults to **false**. Images are stored only after explicit opt-in. Exports omit emails and tokens. API keys are never written into training files.
