from pathlib import Path

import joblib
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from ml.preprocessing import (
    DROP_COLS,
    FEATURE_COLS,
    build_preprocessor,
    clean_leads,
    prepare_xy,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BACKEND_DIR.parent / "leads.csv"
MODEL_PATH = BACKEND_DIR / "models" / "conversion_model.joblib"

_saved_model = None


class LeadScoreRequest(BaseModel):
    source: str = "Facebook Ads"
    city: str = "Islamabad"
    area: str = "Bahria Town"
    property_type: str = "Apartment"
    budget_pkr_lac: float = Field(200.0, ge=0)
    bedrooms: float | None = 2
    first_response_minutes: float = 30
    calls_made: int = 1
    total_call_seconds: float = 120
    whatsapp_replies: int = 1
    site_visits: int = 0
    agent_experience_years: float = 2.0
    is_overseas: int = 0
    referred_by_existing_client: int = 0
    has_financing_approved: int = 0


def load_model():
    global _saved_model
    if _saved_model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"No model at {MODEL_PATH}. Run: python train_model.py"
            )
        _saved_model = joblib.load(MODEL_PATH)
    return _saved_model


def score_lead(payload: LeadScoreRequest) -> dict:
    """Return conversion probability for one lead."""
    model = load_model()
    pipe = model["pipeline"]
    threshold = model.get("threshold", 0.5)

    row = {col: getattr(payload, col) for col in FEATURE_COLS}
    if row["bedrooms"] is None:
        row["bedrooms"] = model.get("bedrooms_median", 2.0)

    X = clean_leads(pd.DataFrame([row]))
    prob = float(pipe.predict_proba(X)[0, 1])
    return {
        "conversion_probability": round(prob, 4),
        "likely_to_convert": prob >= threshold,
        "threshold": threshold,
        "model_metric": {
            "name": model.get("metric_name", "average_precision"),
            "value": model.get("metric_value"),
        },
        "features_used": FEATURE_COLS,
    }


def train() -> float:
    """Train a simple logistic regression baseline and save it."""
    df = pd.read_csv(CSV_PATH)
    X, y = prepare_xy(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipe = Pipeline(
        [
            ("preprocess", build_preprocessor()),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    pipe.fit(X_train, y_train)

    probs = pipe.predict_proba(X_test)[:, 1]
    ap = average_precision_score(y_test, probs)
    preds = (probs >= 0.5).astype(int)

    print("Class balance:")
    print(y.value_counts(normalize=True).round(3).to_string())
    print(f"\nAverage Precision (PR-AUC) = {ap:.4f}")
    print("Why this metric: only ~7% convert, so accuracy is misleading.")
    print(classification_report(y_test, preds, digits=3))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipe,
            "threshold": 0.5,
            "metric_name": "average_precision",
            "metric_value": round(float(ap), 4),
            "bedrooms_median": float(X_train["bedrooms"].median()),
            "feature_columns": FEATURE_COLS,
            "dropped_columns": DROP_COLS,
        },
        MODEL_PATH,
    )
    print(f"Saved model -> {MODEL_PATH}")
    return float(ap)


if __name__ == "__main__":
    train()
