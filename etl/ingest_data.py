import os
import pandas as pd
import logging


def creating_logger():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(), 
            logging.FileHandler("logs/ingest.log", mode="a", encoding="utf-8")  # save to file
        ],
    )
    logger = logging.getLogger("ingest")
    return logger


base_dir = os.path.dirname(os.path.abspath(__file__))  # directory where this script lives
datasets_dir = os.path.join(os.path.dirname(base_dir), "datasets") # points to /etl/datasets/

doctors_path = os.path.join(
    datasets_dir,
    "Data Enginner Doctors Excel - VIP Medical Group.xlsx"
)

appointments_path = os.path.join(
    datasets_dir,
    "Data Engineer Appointments Excel - VIP Medical Group.xlsx"
)

def extract_data(doctors_path: str, appointments_path: str):
    """
    Read both Excel files and return them as DataFrames.
    No transformations, no database upload yet.
    """
    logger = creating_logger()
    logger.info("=== START: INGEST ===")

    # Read doctors.xlsx
    logger.info(f"Reading doctors file from: {doctors_path}")
    doctors_df = pd.read_excel(doctors_path, engine="openpyxl")
    logger.info(f"Doctors file loaded: {len(doctors_df)} rows")

    # Read appointments.xlsx
    logger.info(f"Reading appointments file from: {appointments_path}")
    appointments_df = pd.read_excel(appointments_path, engine="openpyxl")
    logger.info(f"Appointments file loaded: {len(appointments_df)} rows")

    logger.info("=== END: INGEST ===")

    return doctors_df, appointments_df


if __name__ == "__main__":
    doctors_df, appointments_df = extract_data(doctors_path, appointments_path)

    print("\n=== Doctors sample ===")
    print(doctors_df.head())

    print("\n=== Appointments sample ===")
    print(appointments_df.head())

