import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DROP_COLS = [
    "lead_id",
    "crm_record_hash",
    "token_amount_received_pkr",
    "created_at",
]

CATEGORICAL = ["source", "city", "area", "property_type"]

NUMERIC = [
    "budget_pkr_lac",
    "bedrooms",
    "first_response_minutes",
    "calls_made",
    "total_call_seconds",
    "whatsapp_replies",
    "site_visits",
    "agent_experience_years",
    "is_overseas",
    "referred_by_existing_client",
    "has_financing_approved",
]

FEATURE_COLS = CATEGORICAL + NUMERIC

CITY_ALIASES = {
    "islamabad": "Islamabad",
    "rawalpindi": "Rawalpindi",
    "lahore": "Lahore",
    "karachi": "Karachi",
    "peshawar": "Peshawar",
    "faisalabad": "Faisalabad",
    "multan": "Multan",
    "gujranwala": "Gujranwala",
    "abbottabad": "Abbottabad",
}


def normalize_city(value):
    """Fix inconsistent city casing (e.g. ISLAMABAD -> Islamabad).
    Short forms like ISB / Rwp / khi are left unchanged.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    text = str(value).strip()
    if not text:
        return value
    key = text.lower()
    return CITY_ALIASES.get(key, text)


def normalize_label(value):
    """Trim spaces; keep normal title-style labels consistent."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return value
    text = " ".join(str(value).split())
    return text


def clean_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Fix inconsistent spellings before training or scoring."""
    out = df.copy()
    if "city" in out.columns:
        out["city"] = out["city"].map(normalize_city)
    for col in ["source", "area", "property_type"]:
        if col in out.columns:
            out[col] = out[col].map(normalize_label)
    return out


def prepare_xy(df: pd.DataFrame):
    """Clean spellings, then split into features X and target y."""
    cleaned = clean_leads(df)
    y = cleaned["converted"].astype(int)
    X = cleaned.drop(columns=DROP_COLS + ["converted"])
    return X, y


def build_preprocessor():
    """Fill missing values, one-hot categories, scale numbers."""
    cat_steps = Pipeline(
        [
            ("fill", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    num_steps = Pipeline(
        [
            ("fill", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        [
            ("cat", cat_steps, CATEGORICAL),
            ("num", num_steps, NUMERIC),
        ]
    )
