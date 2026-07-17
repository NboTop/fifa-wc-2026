"""
Downloads model files from Hugging Face Hub on startup if they
don't already exist locally. This lets the repo stay small while
still working in production (Render, etc).
"""

import os
from pathlib import Path
from huggingface_hub import hf_hub_download

MODELS_DIR = Path(__file__).parent.parent / "models"
REPO_ID    = "void-logic/wc2026-models"

FILES = [
    "rf_model.pkl",
    "xgb_model.pkl",
    "match_history.pkl",
    "label_encoder.pkl",
    "elo_ratings.pkl",
    "player_kmeans.pkl",
    "player_scaler.pkl",
]


def ensure_models_downloaded():
    MODELS_DIR.mkdir(exist_ok=True)

    for fname in FILES:
        local_path = MODELS_DIR / fname
        if local_path.exists():
            continue

        print(f"Downloading {fname} from Hugging Face...")
        downloaded = hf_hub_download(
            repo_id=REPO_ID,
            filename=fname,
            local_dir=str(MODELS_DIR),
        )
        print(f"  ✓ {fname} ready")

    print("✓ All model files present")