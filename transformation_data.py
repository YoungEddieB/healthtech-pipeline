import sys
import importlib
import os
import pandas as pd
import logging
import numpy as np
import re

# Remove old imports to avoid cache issues
if 'ingest_data' in sys.modules:
    del sys.modules['ingest_data']

# Add the correct folder to sys.path
sys.path.append("/Users/youngeddieb/PycharmProjects/BI-Analytics/BI-Analytics/Pipeline")

import ingest_data
importlib.reload(ingest_data)

print(ingest_data.__file__)
print(dir(ingest_data))

doctors_df, appointments_df = ingest_data.extract_data(ingest_data.doctors_path,ingest_data.appointments_path)
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
    """
    Clean and standardize appointments data.
    """
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

    # --- Fix dates: normalize formats and correct invalid years ---
    if "appointment_date" in df.columns:
        import re

        def fix_date(date_str):
            date_str = str(date_str).strip()
            # Match possible formats
            match = (
                re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str) or   # MM/DD/YYYY
                re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str) or   # YYYY-MM-DD
                re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)      # YYYY/MM/DD
            )

            if match:
                groups = match.groups()
                if '/' in date_str and date_str.index('/') < 3:  # MM/DD/YYYY
                    month, day, year = groups
                else:  # YYYY-MM-DD or YYYY/MM/DD
                    year, month, day = groups

                year = '2025' if int(year) > 2025 else year
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            return date_str  # leave untouched if no pattern matches

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

    # --- Add ingestion timestamp ---
    df["ingested_at"] = pd.Timestamp.utcnow()

    return df

if __name__ == "__main__":
    # assume: sys, logger, extract_data, transform_doctors, transform_appointments already available

    # Keep your existing path append & import
    sys.path.append("/Users/youngeddieb/PyCharmProjects/BI-Analytics/BI-Analytics/Pipeline")
    from ingest_data import extract_data

    # Paths
    project_root = "/Users/youngeddieb/PyCharmProjects/BI-Analytics/BI-Analytics/Pipeline"
    doctors_path = f"{project_root}/datasets/Data Enginner's Doctors Excel - VIP Medical Group.xlsx"
    appointments_path = f"{project_root}/datasets/Data Engineer's Appointments Excel - VIP Medical Group.xlsx"

    # 1) Extract
    doctors_df, appointments_df = extract_data(doctors_path, appointments_path)

    # 2) Transform (kept only in memory)
    doctors_clean = transform_doctors(doctors_df)
    appointments_clean = transform_appointments(appointments_df)

    # 3) Print previews (no CSV writes)
    logger.info("Transformations complete. Holding DataFrames in memory.")

    print("\n=== Doctors (shape: {} rows x {} cols) ===".format(*doctors_clean.shape))
    print(doctors_clean.head())

    print("\n=== Appointments (shape: {} rows x {} cols) ===".format(*appointments_clean.shape))
    print(appointments_clean.head())

    # 4) Optional: Save output DataFrames as CSVs
    output_dir = f"{project_root}/output"
    os.makedirs(output_dir, exist_ok=True)

    doctors_output_path = f"{output_dir}/doctors_clean.csv"
    appointments_output_path = f"{output_dir}/appointments_clean.csv"

    doctors_clean.to_csv(doctors_output_path, index=False)
    appointments_clean.to_csv(appointments_output_path, index=False)

    logger.info(f"Saved transformed datasets to: {output_dir}")
    print(f"\nSaved files:\n- {doctors_output_path}\n- {appointments_output_path}")
