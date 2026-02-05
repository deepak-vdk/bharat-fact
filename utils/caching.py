"""Caching utilities for verification results and model information."""

import json
import hashlib
import re
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

import streamlit as st

# Cache configuration
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "verification_cache.json"
MODEL_CACHE_FILE = CACHE_DIR / "model_cache.json"
MAX_CACHE_SIZE = 100  # Maximum number of cached verifications
CACHE_TTL_DAYS = 30  # Cache expires after 30 days


def normalize_claim(text: str) -> str:
    """Normalize claim text for consistent hashing."""
    return re.sub(r'\s+', ' ', text.strip().lower())


def claim_hash(text: str) -> str:
    """Generate SHA256 hash for a news claim."""
    normalized = normalize_claim(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_model_cache() -> Dict[str, Any]:
    """Load cached model information to avoid repeated list_models calls."""
    if not MODEL_CACHE_FILE.exists():
        return {}
    try:
        with open(MODEL_CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            # Check if cache is still valid (24 hour TTL)
            if cache_data.get("timestamp"):
                cache_time = datetime.fromisoformat(cache_data["timestamp"])
                if datetime.now() - cache_time < timedelta(hours=24):
                    return cache_data
        return {}
    except Exception:
        return {}


def save_model_cache(model_name: str, available_models: List[str]) -> None:
    """Save model information to cache."""
    try:
        cache_data = {
            "model_name": model_name,
            "available_models": available_models,
            "timestamp": datetime.now().isoformat()
        }
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=CACHE_DIR, delete=False
        ) as tmp:
            json.dump(cache_data, tmp, ensure_ascii=False, indent=2)
            os.replace(tmp.name, MODEL_CACHE_FILE)
    except Exception:
        pass


def load_verification_cache() -> Dict[str, Any]:
    """Load verification cache with TTL filtering."""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            # Filter expired entries
            filtered_cache = {}
            for key, value in cache_data.items():
                if isinstance(value, dict) and "timestamp" in value:
                    cache_time = datetime.fromisoformat(value["timestamp"])
                    if datetime.now() - cache_time < timedelta(days=CACHE_TTL_DAYS):
                        filtered_cache[key] = value
                else:
                    # Legacy entries without timestamp - keep for now
                    filtered_cache[key] = value
            return filtered_cache
    except Exception as e:
        st.warning(f"Failed to load cache: {e}")
        return {}


def save_verification_cache(cache: Dict[str, Any]) -> None:
    """
    Safely save cache using atomic write to prevent corruption.
    Enforces size limit and adds timestamps.
    """
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        
        # Add timestamp to new entries and enforce size limit
        # Keep only the most recent MAX_CACHE_SIZE entries
        if len(cache) > MAX_CACHE_SIZE:
            # Sort by timestamp (newest first) and keep top MAX_CACHE_SIZE
            sorted_items = sorted(
                cache.items(),
                key=lambda x: x[1].get("timestamp", ""),
                reverse=True
            )[:MAX_CACHE_SIZE]
            cache = dict(sorted_items)
        
        # Ensure all entries have timestamps
        current_time = datetime.now().isoformat()
        for key, value in cache.items():
            if isinstance(value, dict) and "timestamp" not in value:
                value["timestamp"] = current_time

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CACHE_DIR,
            delete=False
        ) as tmp:
            json.dump(cache, tmp, ensure_ascii=False, indent=2)
            temp_name = tmp.name

        # Atomic replace
        os.replace(temp_name, CACHE_FILE)

    except Exception as e:
        st.warning(f"Failed to safely save cache: {e}")


# Export cache file paths for use in other modules
__all__ = [
    'load_verification_cache',
    'save_verification_cache',
    'load_model_cache',
    'save_model_cache',
    'claim_hash',
    'normalize_claim',
    'MODEL_CACHE_FILE',
    'CACHE_FILE',
    'CACHE_DIR'
]

