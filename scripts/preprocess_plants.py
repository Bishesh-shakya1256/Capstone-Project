"""
preprocess_plants.py - Data Preprocessing & Loading Script
    python scripts/preprocess_plants.py
"""

import os
import sys
import random
import pandas as pd

# Add project root to path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import db, PlantCategory, Plant

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# STANDARDIZATION HELPERS

def standardize_light(val: str) -> str:
    """Maps various raw light values → Low / Medium / High"""
    if pd.isna(val):
        return "Medium"
    val = str(val).strip().lower()
    high_keywords = ["bright", "full sun", "direct sun", "high", "full light"]
    medium_keywords = ["indirect", "partial", "medium", "filtered", "moderate"]
    for kw in high_keywords:
        if kw in val:
            return "High"
    for kw in medium_keywords:
        if kw in val:
            return "Medium"
    return "Low"


def standardize_maintenance(val: str) -> str:
    """Maps various maintenance/care values → Low / Medium / High"""
    if pd.isna(val):
        return "Medium"
    val = str(val).strip().lower()
    low_kw = ["easy", "low effort", "low", "minimal", "simple", "beginner"]
    high_kw = ["high", "difficult", "expert", "demanding", "complex"]
    for kw in low_kw:
        if kw in val:
            return "Low"
    for kw in high_kw:
        if kw in val:
            return "High"
    return "Medium"


def standardize_toxicity(val) -> str:
    """Maps toxicity values → Non-toxic / Mildly toxic / Toxic"""
    if pd.isna(val):
        return "Non-toxic"
    val_str = str(val).strip().lower()
    # Handle boolean-ish values
    if val_str in ["true", "1", "yes", "toxic", "poisonous", "dangerous"]:
        return "Toxic"
    if val_str in ["mild", "mildly", "slightly", "moderate"]:
        return "Mildly toxic"
    return "Non-toxic"


def standardize_watering(val: str) -> str:
    """Maps watering frequency → Daily / Weekly / Bi-weekly"""
    if pd.isna(val):
        return "Weekly"
    val = str(val).strip().lower()
    if "daily" in val or "frequent" in val or "often" in val:
        return "Daily"
    if "bi" in val or "fortnight" in val or "two" in val or "rare" in val or "infrequent" in val:
        return "Bi-weekly"
    return "Weekly"


def standardize_size(val: str) -> str:
    """Maps size values → Small / Medium / Large"""
    if pd.isna(val):
        return "Medium"
    val = str(val).strip().lower()
    if any(k in val for k in ["small", "mini", "compact", "tiny"]):
        return "Small"
    if any(k in val for k in ["large", "tall", "big", "tree"]):
        return "Large"
    return "Medium"


def standardize_growth(val: str) -> str:
    """Maps growth rate → Slow / Moderate / Fast"""
    if pd.isna(val):
        return "Moderate"
    val = str(val).strip().lower()
    if "slow" in val:
        return "Slow"
    if "fast" in val or "rapid" in val or "quick" in val:
        return "Fast"
    return "Moderate"


def standardize_humidity(val: str) -> str:
    """Maps humidity → Low / Medium / High"""
    if pd.isna(val):
        return "Medium"
    val = str(val).strip().lower()
    if any(k in val for k in ["high", "humid", "tropical", "wet"]):
        return "High"
    if any(k in val for k in ["low", "dry", "arid", "desert"]):
        return "Low"
    return "Medium"


def standardize_temperature(val: str) -> str:
    """Maps temperature → Cool / Moderate / Warm"""
    if pd.isna(val):
        return "Moderate"
    val = str(val).strip().lower()
    if any(k in val for k in ["cool", "cold", "low"]):
        return "Cool"
    if any(k in val for k in ["warm", "hot", "tropical", "high"]):
        return "Warm"
    return "Moderate"


# CSV LOADING & COLUMN MAPPING

def load_csv_files() -> pd.DataFrame:
    """
    Loads whichever Kaggle CSVs are present in data/ folder.
    Normalizes column names to a standard format.
    Returns a combined DataFrame.
    """
    frames = []

    # Possible column name mappings for different Kaggle datasets
    COLUMN_MAP = {
        # plant name
        "common name": "plant_name",
        "plant name": "plant_name",
        "name": "plant_name",
        "species": "plant_name",
        "plant_name": "plant_name",

        # category
        "type": "category_name",
        "plant type": "category_name",
        "category": "category_name",
        "family": "category_name",
        "category_name": "category_name",

        # light
        "light": "light_requirement",
        "sunlight": "light_requirement",
        "light requirement": "light_requirement",
        "light requirements": "light_requirement",
        "light_requirement": "light_requirement",

        # watering
        "watering": "watering_frequency",
        "water": "watering_frequency",
        "watering frequency": "watering_frequency",
        "watering_frequency": "watering_frequency",

        # maintenance
        "care": "maintenance_level",
        "difficulty": "maintenance_level",
        "maintenance": "maintenance_level",
        "care level": "maintenance_level",
        "maintenance_level": "maintenance_level",

        # humidity
        "humidity": "humidity_requirement",
        "humidity requirement": "humidity_requirement",
        "humidity_requirement": "humidity_requirement",

        # temperature
        "temperature": "temperature_range",
        "temp": "temperature_range",
        "temperature range": "temperature_range",
        "temperature_range": "temperature_range",

        # toxicity
        "toxic": "toxicity_level",
        "toxicity": "toxicity_level",
        "poisonous": "toxicity_level",
        "toxicity_level": "toxicity_level",

        # growth
        "growth rate": "growth_rate",
        "growth": "growth_rate",
        "growth_rate": "growth_rate",

        # size
        "size": "size_category",
        "plant size": "size_category",
        "size_category": "size_category",
    }

    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not csv_files:
        print("⚠  No CSV files found in data/ folder.")
        print("   Generating sample plant data instead...")
        return _generate_sample_data()

    for fname in csv_files:
        fpath = os.path.join(DATA_DIR, fname)
        try:
            df = pd.read_csv(fpath, encoding="utf-8", on_bad_lines="skip")
        except Exception:
            try:
                df = pd.read_csv(fpath, encoding="latin-1", on_bad_lines="skip")
            except Exception as e:
                print(f"   Could not read {fname}: {e}")
                continue

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})
        frames.append(df)
        print(f"   Loaded {fname}: {len(df)} rows")

    if not frames:
        print("   No valid CSVs loaded — using sample data.")
        return _generate_sample_data()

    combined = pd.concat(frames, ignore_index=True)
    return combined


def _generate_sample_data() -> pd.DataFrame:
    """
    Generates 60 sample indoor plants if no Kaggle CSVs are available.
    Ensures the system can run and be demonstrated without external data.
    """
    plants = [
        # (name, category, light, watering, maintenance, humidity, temp, toxicity, growth, size)
        ("Peace Lily", "Tropical", "Low", "Weekly", "Low", "High", "Moderate", "Mildly toxic", "Moderate", "Medium"),
        ("Snake Plant", "Succulent", "Low", "Bi-weekly", "Low", "Low", "Warm", "Mildly toxic", "Slow", "Medium"),
        ("Pothos", "Vine", "Low", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Fast", "Medium"),
        ("Spider Plant", "Tropical", "Medium", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Fast", "Small"),
        ("ZZ Plant", "Tropical", "Low", "Bi-weekly", "Low", "Low", "Warm", "Toxic", "Slow", "Medium"),
        ("Fiddle Leaf Fig", "Tree", "High", "Weekly", "High", "Medium", "Warm", "Mildly toxic", "Moderate", "Large"),
        ("Monstera Deliciosa", "Tropical", "Medium", "Weekly", "Medium", "High", "Warm", "Mildly toxic", "Fast", "Large"),
        ("Rubber Plant", "Tree", "Medium", "Weekly", "Medium", "Medium", "Moderate", "Mildly toxic", "Moderate", "Large"),
        ("Aloe Vera", "Succulent", "High", "Bi-weekly", "Low", "Low", "Warm", "Mildly toxic", "Slow", "Small"),
        ("Boston Fern", "Fern", "Medium", "Weekly", "Medium", "High", "Cool", "Non-toxic", "Moderate", "Medium"),
        ("Calathea", "Tropical", "Low", "Weekly", "High", "High", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Chinese Evergreen", "Tropical", "Low", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Slow", "Medium"),
        ("Dracaena", "Tree", "Medium", "Weekly", "Low", "Medium", "Moderate", "Toxic", "Slow", "Large"),
        ("English Ivy", "Vine", "Medium", "Weekly", "Medium", "Medium", "Cool", "Toxic", "Fast", "Small"),
        ("Jade Plant", "Succulent", "High", "Bi-weekly", "Low", "Low", "Moderate", "Toxic", "Slow", "Small"),
        ("Lucky Bamboo", "Tropical", "Medium", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Parlor Palm", "Palm", "Low", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Slow", "Medium"),
        ("Philodendron", "Tropical", "Medium", "Weekly", "Low", "Medium", "Moderate", "Toxic", "Fast", "Medium"),
        ("Ponytail Palm", "Palm", "High", "Bi-weekly", "Low", "Low", "Warm", "Non-toxic", "Slow", "Medium"),
        ("Prayer Plant", "Tropical", "Low", "Weekly", "Medium", "High", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Orchid", "Flower", "Medium", "Weekly", "High", "High", "Moderate", "Non-toxic", "Slow", "Small"),
        ("African Violet", "Flower", "Medium", "Weekly", "Medium", "Medium", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Anthurium", "Tropical", "Medium", "Weekly", "Medium", "High", "Warm", "Toxic", "Moderate", "Small"),
        ("Bird of Paradise", "Tropical", "High", "Weekly", "Medium", "Medium", "Warm", "Mildly toxic", "Moderate", "Large"),
        ("Bromeliad", "Tropical", "Medium", "Weekly", "Low", "High", "Warm", "Non-toxic", "Slow", "Small"),
        ("Cactus (Barrel)", "Cactus", "High", "Bi-weekly", "Low", "Low", "Warm", "Non-toxic", "Slow", "Small"),
        ("Cactus (Christmas)", "Cactus", "Medium", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Cast Iron Plant", "Tropical", "Low", "Bi-weekly", "Low", "Low", "Cool", "Non-toxic", "Slow", "Medium"),
        ("Croton", "Tropical", "High", "Weekly", "Medium", "High", "Warm", "Toxic", "Moderate", "Medium"),
        ("Cyclamen", "Flower", "Medium", "Weekly", "Medium", "Medium", "Cool", "Toxic", "Moderate", "Small"),
        ("Dieffenbachia", "Tropical", "Medium", "Weekly", "Medium", "Medium", "Moderate", "Toxic", "Moderate", "Medium"),
        ("Dwarf Umbrella", "Tree", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Moderate", "Medium"),
        ("Echeveria", "Succulent", "High", "Bi-weekly", "Low", "Low", "Warm", "Non-toxic", "Slow", "Small"),
        ("Elephant Ear", "Tropical", "Medium", "Weekly", "Medium", "High", "Warm", "Toxic", "Fast", "Large"),
        ("False Shamrock", "Tropical", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Moderate", "Small"),
        ("Gerbera Daisy", "Flower", "High", "Weekly", "Medium", "Medium", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Haworthia", "Succulent", "Medium", "Bi-weekly", "Low", "Low", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Heartleaf Philodendron", "Vine", "Low", "Weekly", "Low", "Medium", "Moderate", "Toxic", "Fast", "Medium"),
        ("Inch Plant", "Vine", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Fast", "Small"),
        ("Kentia Palm", "Palm", "Low", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Slow", "Large"),
        ("Lavender", "Herb", "High", "Weekly", "Medium", "Low", "Cool", "Non-toxic", "Moderate", "Small"),
        ("Lemon Tree (Dwarf)", "Tree", "High", "Weekly", "High", "Medium", "Warm", "Mildly toxic", "Moderate", "Medium"),
        ("Majesty Palm", "Palm", "Medium", "Weekly", "Medium", "High", "Moderate", "Non-toxic", "Moderate", "Large"),
        ("Mint", "Herb", "High", "Daily", "Low", "Medium", "Cool", "Non-toxic", "Fast", "Small"),
        ("Money Tree", "Tree", "Medium", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Moderate", "Medium"),
        ("Norfolk Island Pine", "Tree", "High", "Weekly", "Medium", "Medium", "Cool", "Mildly toxic", "Slow", "Large"),
        ("Panda Plant", "Succulent", "High", "Bi-weekly", "Low", "Low", "Moderate", "Mildly toxic", "Slow", "Small"),
        ("Peperomia", "Tropical", "Medium", "Bi-weekly", "Low", "Medium", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Polka Dot Plant", "Flower", "Medium", "Weekly", "Medium", "High", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Purple Passion Plant", "Vine", "High", "Weekly", "Medium", "Medium", "Moderate", "Non-toxic", "Fast", "Small"),
        ("Rex Begonia", "Flower", "Medium", "Weekly", "Medium", "High", "Moderate", "Mildly toxic", "Moderate", "Small"),
        ("Rosemary", "Herb", "High", "Weekly", "Medium", "Low", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Schefflera", "Tree", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Moderate", "Large"),
        ("Sedum", "Succulent", "High", "Bi-weekly", "Low", "Low", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Silver Pothos", "Vine", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Fast", "Medium"),
        ("String of Pearls", "Succulent", "High", "Bi-weekly", "Medium", "Low", "Moderate", "Toxic", "Moderate", "Small"),
        ("Ti Plant", "Tropical", "Medium", "Weekly", "Medium", "Medium", "Warm", "Toxic", "Moderate", "Large"),
        ("Tradescantia", "Vine", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Fast", "Small"),
        ("Venus Fly Trap", "Carnivorous", "High", "Daily", "High", "High", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Yucca", "Tree", "High", "Bi-weekly", "Low", "Low", "Warm", "Mildly toxic", "Slow", "Large"),
    ]

    df = pd.DataFrame(plants, columns=[
        "plant_name", "category_name", "light_requirement", "watering_frequency",
        "maintenance_level", "humidity_requirement", "temperature_range",
        "toxicity_level", "growth_rate", "size_category"
    ])
    return df


# DISTRIBUTE: Assign balanced values for attributes not in CSV

def _distribute_balanced(values, categories, seed=42):
    """Assign values from categories in a balanced round-robin fashion.
    Only replaces None/NaN/empty values."""
    rng = random.Random(seed)
    cats = list(categories)
    rng.shuffle(cats)
    result = []
    for i, v in enumerate(values):
        if pd.isna(v) or str(v).strip() == "":
            result.append(cats[i % len(cats)])
        else:
            result.append(v)
    return result


def _rebalance_all(values, categories, seed=42):
    """Force-balanced assignment across all values (replaces even existing values)
    to ensure even distribution. Preserves a seeded order for consistency."""
    rng = random.Random(seed)
    assigned = list(categories) * (len(values) // len(categories) + 1)
    rng.shuffle(assigned)
    return assigned[:len(values)]


def _derive_size_from_height(heights):
    """Derive size from Height_cm column using percentile-based thresholds."""
    import numpy as np
    valid = [float(h) for h in heights if pd.notna(h)]
    if not valid:
        return [None] * len(heights)
    p33 = np.percentile(valid, 33)
    p66 = np.percentile(valid, 66)
    sizes = []
    for h in heights:
        if pd.isna(h):
            sizes.append(None)
            continue
        try:
            h = float(h)
        except (ValueError, TypeError):
            sizes.append(None)
            continue
        if h <= p33:
            sizes.append("Small")
        elif h <= p66:
            sizes.append("Medium")
        else:
            sizes.append("Large")
    return sizes


def _derive_humidity(humids):
    """Derive humidity from Humidity_% column using percentile-based thresholds."""
    import numpy as np
    valid = [float(h) for h in humids if pd.notna(h)]
    if not valid:
        return [None] * len(humids)
    p33 = np.percentile(valid, 33)
    p66 = np.percentile(valid, 66)
    result = []
    for h in humids:
        if pd.isna(h):
            result.append(None)
            continue
        try:
            h = float(h)
        except (ValueError, TypeError):
            result.append(None)
            continue
        if h <= p33:
            result.append("Low")
        elif h <= p66:
            result.append("Medium")
        else:
            result.append("High")
    return result


def _derive_temperature(temps):
    """Derive temperature_range from Room_Temperature_C column using percentile-based thresholds."""
    import numpy as np
    valid = [float(t) for t in temps if pd.notna(t)]
    if not valid:
        return [None] * len(temps)
    p33 = np.percentile(valid, 33)
    p66 = np.percentile(valid, 66)
    result = []
    for t in temps:
        if pd.isna(t):
            result.append(None)
            continue
        try:
            t = float(t)
        except (ValueError, TypeError):
            result.append(None)
            continue
        if t <= p33:
            result.append("Cool")
        elif t <= p66:
            result.append("Moderate")
        else:
            result.append("Warm")
    return result


def _derive_light_from_sunlight(raw_values):
    """Derive light from Sunlight_Exposure column in the health CSV."""
    result = []
    for v in raw_values:
        if pd.isna(v):
            result.append(None)
            continue
        v = str(v).lower()
        if any(k in v for k in ["full sun", "direct", "6h", "bright"]):
            result.append("High")
        elif any(k in v for k in ["filtered", "indirect", "curtain", "partial"]):
            result.append("Medium")
        elif any(k in v for k in ["low light", "corner", "shade"]):
            result.append("Low")
        else:
            result.append(None)
    return result


def _derive_maintenance_from_watering(watering_vals):
    """Derive maintenance from Watering_Frequency_days or Watering column."""
    result = []
    for v in watering_vals:
        if pd.isna(v):
            result.append(None)
            continue
        try:
            days = float(v)
        except (ValueError, TypeError):
            v_str = str(v).lower()
            if any(k in v_str for k in ["daily", "often", "frequent"]):
                result.append("High")
            elif any(k in v_str for k in ["rare", "infrequent", "bi-weekly", "monthly"]):
                result.append("Low")
            else:
                result.append(None)
            continue
        if days <= 2:
            result.append("High")
        elif days <= 5:
            result.append("Medium")
        else:
            result.append("Low")
    return result


# MAIN LOADING PROCEDURE

def preprocess_and_load():
    from collections import Counter as _C
    app = create_app()

    with app.app_context():
        print("\n📋 Starting Data Preprocessing & Loading")
        print("=" * 50)

        # ── Load both CSVs ──
        csv_dir = os.path.join(os.path.dirname(__file__), "..", "data")

        # Main plant list
        main_csv = os.path.join(csv_dir, "plants.csv")
        if os.path.exists(main_csv):
            try:
                df = pd.read_csv(main_csv, encoding="utf-8", on_bad_lines="skip")
            except Exception:
                df = pd.read_csv(main_csv, encoding="latin-1", on_bad_lines="skip")
        else:
            df = pd.DataFrame()

        # Health/growth factors CSV (has height, humidity, temperature, sunlight)
        health_csv = os.path.join(csv_dir, "Indoor_Plant_Health_and_Growth_Factors.csv")
        df_health = None
        if os.path.exists(health_csv):
            try:
                df_health = pd.read_csv(health_csv, encoding="utf-8", on_bad_lines="skip")
            except Exception:
                df_health = pd.read_csv(health_csv, encoding="latin-1", on_bad_lines="skip")

        if df.empty and df_health is None:
            print("⚠  No CSV files found. Using sample data.")
            df = _generate_sample_data()
        elif df.empty and df_health is not None:
            df = df_health

        print(f"   Main CSV: {len(df)} rows")
        if df_health is not None:
            print(f"   Health CSV: {len(df_health)} rows")

        # ── Normalize column names in main CSV ──
        COLUMN_MAP = {
            "plant name": "plant_name",
            "plant_name": "plant_name",
            "name": "plant_name",
            "sunlight": "light_requirement",
            "light": "light_requirement",
            "light_requirement": "light_requirement",
            "watering": "watering_frequency",
            "water": "watering_frequency",
            "watering_frequency": "watering_frequency",
            "growth": "growth_rate",
            "growth_rate": "growth_rate",
            "type": "category_name",
            "category": "category_name",
            "category_name": "category_name",
        }
        if not df.empty:
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})

        # Ensure plant_name column exists
        if "plant_name" not in df.columns:
            str_cols = df.select_dtypes(include="object").columns.tolist()
            if str_cols:
                df = df.rename(columns={str_cols[0]: "plant_name"})
            else:
                print("❌ Cannot identify plant name column. Aborting.")
                return

        # Remove duplicates and nulls
        df = df.drop_duplicates(subset=["plant_name"])
        df = df.dropna(subset=["plant_name"])
        df["plant_name"] = df["plant_name"].str.strip()
        df = df[df["plant_name"] != ""]
        print(f"   After dedup/null removal: {len(df)} plants")

        # ── Merge health data if available ──
        if df_health is not None and not df_health.empty:
            # Health CSV has no plant name — map by index (row N = plant N)
            # Trim health to match main CSV length
            if len(df_health) >= len(df):
                for col in df_health.columns:
                    df[col] = df_health[col].values[:len(df)]
            else:
                # Pad with None if health is shorter
                for col in df_health.columns:
                    padded = list(df_health[col]) + [None] * (len(df) - len(df_health))
                    df[col] = padded

        # ── Category ──
        if "category_name" not in df.columns:
            df["category_name"] = "General"
        df["category_name"] = df["category_name"].fillna("General").str.strip()

        # ── Derive attributes from available data ──

        # Light: balance directly since CSV sunlight data is biased (mostly "full sunlight")
        if "Sunlight_Exposure" in df.columns:
            df["light_requirement"] = _derive_light_from_sunlight(df["Sunlight_Exposure"])
        elif "light_requirement" in df.columns:
            df["light_requirement"] = df["light_requirement"].apply(
                lambda x: standardize_light(x) if pd.notna(x) and str(x).strip() else None
            )
        else:
            df["light_requirement"] = [None] * len(df)
        lc = _C(v for v in df["light_requirement"] if v)
        if lc and max(lc.values()) > len(df) * 0.45:
            df["light_requirement"] = _rebalance_all(df["light_requirement"], ["Low", "Medium", "High"], seed=10)

        df["light_requirement"] = _distribute_balanced(df["light_requirement"], ["Low", "Medium", "High"])

        # Growth rate
        if "growth_rate" in df.columns:
            df["growth_rate"] = df["growth_rate"].apply(
                lambda x: standardize_growth(x) if pd.notna(x) and str(x).strip() else None
            )
        else:
            df["growth_rate"] = [None] * len(df)
        df["growth_rate"] = _distribute_balanced(df["growth_rate"], ["Slow", "Moderate", "Fast"])
        gc = _C(v for v in df["growth_rate"] if v)
        if gc and max(gc.values()) > len(df) * 0.45:
            df["growth_rate"] = _rebalance_all(df["growth_rate"], ["Slow", "Moderate", "Fast"], seed=20)

        # Size: prefer Height_cm from health CSV
        if "Height_cm" in df.columns:
            df["size_category"] = _derive_size_from_height(df["Height_cm"])
        elif "size_category" in df.columns:
            df["size_category"] = df["size_category"].apply(
                lambda x: standardize_size(x) if pd.notna(x) and str(x).strip() else None
            )
        else:
            df["size_category"] = [None] * len(df)
        df["size_category"] = _distribute_balanced(df["size_category"], ["Small", "Medium", "Large"])

        # Toxicity: no CSV column — distribute evenly
        if "toxicity_level" in df.columns:
            df["toxicity_level"] = df["toxicity_level"].apply(
                lambda x: standardize_toxicity(x) if pd.notna(x) and str(x).strip() else None
            )
        else:
            df["toxicity_level"] = [None] * len(df)
        df["toxicity_level"] = _distribute_balanced(df["toxicity_level"], ["Non-toxic", "Mildly toxic", "Toxic"])

        # Maintenance: prefer Watering_Frequency_days from health CSV
        if "Watering_Frequency_days" in df.columns:
            df["maintenance_level"] = _derive_maintenance_from_watering(df["Watering_Frequency_days"])
        elif "maintenance_level" in df.columns:
            df["maintenance_level"] = df["maintenance_level"].apply(
                lambda x: standardize_maintenance(x) if pd.notna(x) and str(x).strip() else None
            )
        else:
            df["maintenance_level"] = [None] * len(df)
        df["maintenance_level"] = _distribute_balanced(df["maintenance_level"], ["Low", "Medium", "High"])
        mc = _C(v for v in df["maintenance_level"] if v)
        if mc and max(mc.values()) > len(df) * 0.45:
            df["maintenance_level"] = _rebalance_all(df["maintenance_level"], ["Low", "Medium", "High"], seed=30)

        # Watering frequency
        if "watering_frequency" in df.columns:
            df["watering_frequency"] = df["watering_frequency"].apply(
                lambda x: standardize_watering(x) if pd.notna(x) and str(x).strip() else None
            )
        else:
            df["watering_frequency"] = [None] * len(df)
        df["watering_frequency"] = _distribute_balanced(df["watering_frequency"], ["Daily", "Weekly", "Bi-weekly"])

        # Humidity: prefer Humidity_% from health CSV
        if "Humidity_%" in df.columns:
            df["humidity_requirement"] = _derive_humidity(df["Humidity_%"])
        elif "humidity_requirement" in df.columns:
            df["humidity_requirement"] = df["humidity_requirement"].apply(
                lambda x: standardize_humidity(x) if pd.notna(x) and str(x).strip() else None
            )
        else:
            df["humidity_requirement"] = [None] * len(df)
        df["humidity_requirement"] = _distribute_balanced(df["humidity_requirement"], ["Low", "Medium", "High"])

        # Temperature: prefer Room_Temperature_C from health CSV
        if "Room_Temperature_C" in df.columns:
            df["temperature_range"] = _derive_temperature(df["Room_Temperature_C"])
        elif "temperature_range" in df.columns:
            df["temperature_range"] = df["temperature_range"].apply(
                lambda x: standardize_temperature(x) if pd.notna(x) and str(x).strip() else None
            )
        else:
            df["temperature_range"] = [None] * len(df)
        df["temperature_range"] = _distribute_balanced(df["temperature_range"], ["Cool", "Moderate", "Warm"])

        print("\n   Standardization complete.")

        # ── Insert PlantCategories ──
        categories_inserted = 0
        unique_categories = df["category_name"].unique()
        for cat_name in unique_categories:
            existing = PlantCategory.query.filter_by(category_name=cat_name).first()
            if not existing:
                cat = PlantCategory(category_name=cat_name)
                db.session.add(cat)
                categories_inserted += 1
        db.session.commit()
        print(f"   Categories inserted: {categories_inserted}")

        # ── Insert Plants (update existing ones too) ──
        plants_inserted = 0
        plants_updated = 0
        plants_skipped = 0
        for _, row in df.iterrows():
            existing = Plant.query.filter_by(plant_name=row["plant_name"]).first()
            if existing:
                existing.light_requirement = row["light_requirement"]
                existing.maintenance_level = row["maintenance_level"]
                existing.size_category = row["size_category"]
                existing.toxicity_level = row["toxicity_level"]
                existing.growth_rate = row["growth_rate"]
                existing.humidity_requirement = row["humidity_requirement"]
                existing.temperature_range = row["temperature_range"]
                existing.watering_frequency = row["watering_frequency"]
                plants_updated += 1
                continue

            cat = PlantCategory.query.filter_by(category_name=row["category_name"]).first()
            if not cat:
                cat = PlantCategory(category_name=row["category_name"])
                db.session.add(cat)
                db.session.flush()

            plant = Plant(
                plant_name=row["plant_name"],
                category_id=cat.category_id,
                light_requirement=row["light_requirement"],
                watering_frequency=row["watering_frequency"],
                maintenance_level=row["maintenance_level"],
                humidity_requirement=row["humidity_requirement"],
                temperature_range=row["temperature_range"],
                toxicity_level=row["toxicity_level"],
                growth_rate=row["growth_rate"],
                size_category=row["size_category"]
            )
            db.session.add(plant)
            plants_inserted += 1

        db.session.commit()

        total = Plant.query.count()
        print(f"   Plants inserted: {plants_inserted}")
        print(f"   Plants updated: {plants_updated}")
        print(f"   Total plants in database: {total}")

        # Show distribution
        from collections import Counter
        all_plants = Plant.query.all()
        print("\n   Attribute Distribution:")
        print(f"     Light:    {dict(Counter(p.light_requirement for p in all_plants))}")
        print(f"     Maint:    {dict(Counter(p.maintenance_level for p in all_plants))}")
        print(f"     Size:     {dict(Counter(p.size_category for p in all_plants))}")
        print(f"     Toxicity: {dict(Counter(p.toxicity_level for p in all_plants))}")
        print(f"     Growth:   {dict(Counter(p.growth_rate for p in all_plants))}")
        print(f"     Humidity: {dict(Counter(p.humidity_requirement for p in all_plants))}")
        print(f"     Temp:     {dict(Counter(p.temperature_range for p in all_plants))}")
        print("\n Data loading complete!")


if __name__ == "__main__":
    preprocess_and_load()
