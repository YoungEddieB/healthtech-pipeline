import sys
import importlib
import os
import pandas as pd
import logging
import numpy as np
import re

if 'ingest_data' in sys.modules:
    del sys.modules['ingest_data']

base_dir = os.path.dirname(os.path.abspath(__file__))     
project_root = os.path.dirname(base_dir)          
sys.path.append(base_dir)

import ingest_data
importlib.reload(ingest_data)

print(ingest_data.__file__)
print(dir(ingest_data))

doctors_df, appointments_df = ingest_data.extract_data(
    ingest_data.doctors_path,
    ingest_data.appointments_path
)
doctors_df.head()
appointments_df.head()

logger = logging.getLogger("transform")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names: lowercase, remove spaces/symbols."""
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df

def transform_doctors(doctors_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize doctors data."""
    logger.info("Transforming doctors dataset...")
    df = doctors_df.copy()
    df = normalize_columns(df)

    # --- Rename columns ---
    rename_map = {
        "doctor_id": "doctor_id",
        "name": "doctor_name",
        "specialty": "specialty",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Remove duplicates based on doctor_id if available
    if "doctor_id" in df.columns:
        df = df.drop_duplicates(subset=["doctor_id"], keep="last")

    # Trim string columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Add ingestion timestamp
    df["ingested_at"] = pd.Timestamp.utcnow()

    logger.info(f"Doctors cleaned: {len(df)} rows")
    return df

def transform_appointments(appointments_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize appointments data."""
    logger.info("Transforming appointments dataset...")
    df = appointments_df.copy()
    df = normalize_columns(df)

    # --- Rename columns ---
    rename_map = {
        "booking_id": "appointment_id",
        "patientid": "patient_id",
        "doctorid": "doctor_id",
        "booking_date": "appointment_date",
        "date": "appointment_date",
        "datetime": "appointment_date",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # --- Clean appointment_id (remove non-numeric like 'X') ---
    if "appointment_id" in df.columns:
        df["appointment_id"] = (
            df["appointment_id"].astype(str)
            .str.replace(r"[^0-9]", "", regex=True)
        )
        df["appointment_id"] = pd.to_numeric(df["appointment_id"], errors="coerce").fillna(0).astype(int)

    # --- Convert patient_id and doctor_id to numeric ---
    for col in ["patient_id", "doctor_id"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # --- Fix dates ---
    if "appointment_date" in df.columns:
        import re

        def fix_date(date_str):
            date_str = str(date_str).strip()
            match = (
                re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str) or
                re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str) or
                re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
            )
            if match:
                groups = match.groups()
                if '/' in date_str and date_str.index('/') < 3:
                    month, day, year = groups
                else:
                    year, month, day = groups
                year = '2025' if int(year) > 2025 else year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            return date_str

        df["appointment_date"] = df["appointment_date"].apply(fix_date)
        logger.info("Dates normalized to YYYY-MM-DD format")

    # --- Standardize status values ---
    if "status" in df.columns:
        df["status"] = (
            df["status"]
            .astype(str)
            .str.lower()
            .str.strip()
            .str.rstrip(".")
            .replace({"canceled": "cancelled"})
        )
        logger.info("Status values standardized")

    df["ingested_at"] = pd.Timestamp.utcnow()
    return df


if __name__ == "__main__":
    # --- Dynamically detect paths instead of hardcoding them ---
    datasets_dir = os.path.join(project_root, "datasets")
    output_dir = os.path.join(project_root, "output")

    doctors_path = os.path.join(datasets_dir, "Data Enginner Doctors Excel - VIP Medical Group.xlsx")
    appointments_path = os.path.join(datasets_dir, "Data Engineer Appointments Excel - VIP Medical Group.xlsx")

    from ingest_data import extract_data

    doctors_df, appointments_df = extract_data(doctors_path, appointments_path)

    doctors_clean = transform_doctors(doctors_df)
    appointments_clean = transform_appointments(appointments_df)

    logger.info("Transformations complete. Holding DataFrames in memory.")

    print("\n=== Doctors (shape: {} rows x {} cols) ===".format(*doctors_clean.shape))
    print(doctors_clean.head())

    print("\n=== Appointments (shape: {} rows x {} cols) ===".format(*appointments_clean.shape))
    print(appointments_clean.head())

    os.makedirs(output_dir, exist_ok=True)
    doctors_output_path = os.path.join(output_dir, "doctors_clean.csv")
    appointments_output_path = os.path.join(output_dir, "appointments_clean.csv")

    doctors_clean.to_csv(doctors_output_path, index=False)
    appointments_clean.to_csv(appointments_output_path, index=False)

    logger.info(f"Saved transformed datasets to: {output_dir}")
    print(f"\nSaved files:\n- {doctors_output_path}\n- {appointments_output_path}")


