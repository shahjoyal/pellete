"""
ml/model.py
===========
Drop your trained ML model here and implement the `predict` function.
The function receives a flat dict of floats (built by app._build_feature_vector)
and must return a dict matching the /api/predict response schema.

Example skeleton:
"""

import joblib
import numpy as np
import os

# _MODEL = joblib.load(os.path.join(os.path.dirname(__file__), "pellet_model.pkl"))

FEATURE_ORDER = [
    "plant_capacity", "ore_type", "ore_percent", "feed_rate", "loi",
    "chem_moisture", "chem_fe", "chem_sio2", "chem_al2o3", "chem_blain",
    "chem_mic45", "raw_feed_moisture", "blain", "mill_speed", "retention_time",
    "underflow_density", "thickner_vacuum", "cake_moisture", "filter_vacuum",
    "bentonite_dosage", "ob_dosage", "mix_moisture", "water_addition",
    "disc_angle", "motor_rpm", "disc_rpm", "green_ball_moisture", "water_spray_rate",
    "gb_moisture", "gb_drop_number", "gb_gcs", "gb_size", "gb_porosity",
    "screen_s8_10", "screen_s10_12", "screen_s12_14", "screen_s14_16", "recycled",
    "indu_mode", "indu_rpm", "indu_btt", "indu_drm", "indu_exhaust",
    "tg_rpm", "mc_temp", "tg_discharge", "tg_exhaust",
    "cool_zone1", "cool_zone2", "cool_zone3", "cool_zone4",
]


def predict(features: dict) -> dict:
    """
    Parameters
    ----------
    features : dict
        Output of app._build_feature_vector()

    Returns
    -------
    dict  – must match the `predictions` key in /api/predict response
    """
    # Build numpy array in the correct feature order
    # X = np.array([[features.get(k, 0.0) for k in FEATURE_ORDER]])

    # raw = _MODEL.predict(X)[0]   # shape depends on your model

    raise NotImplementedError("Replace this stub with your actual model logic.")


def load_model(path: str):
    """Utility to load a pickled model at startup."""
    return joblib.load(path)
