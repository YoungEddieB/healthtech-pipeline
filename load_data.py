import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, execute_batch
import sys
import importlib
import logging
import transformation_data
importlib.reload(transformation_data)
from transformation_data import transform_doctors, transform_appointments
from ingest_data import extract_data

try: 
    connection = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='123',
        database='healthtech_db',
    )
    print("connection successfully")
    cursor = connection.cursor()
    cursor.execute("SELECT version()")
    row = cursor.fetchone()
    print(row)
except Exception as ex:
    print(ex)

sys.path.append("/Users/youngeddieb/PyCharmProjects/BI-Analytics/BI-Analytics/Pipeline")

# Define paths
project_root = "/Users/youngeddieb/PyCharmProjects/BI-Analytics/BI-Analytics/Pipeline"
doctors_path = f"{project_root}/datasets/Data Enginner's Doctors Excel - VIP Medical Group.xlsx"
appointments_path = f"{project_root}/datasets/Data Engineer's Appointments Excel - VIP Medical Group.xlsx"

# 1) Extract
doctors_df, appointments_df = extract_data(doctors_path, appointments_path)

# 2) Transform (kept only in memory)
doctors_clean = transform_doctors(doctors_df)
appointments_clean = transform_appointments(appointments_df)

# 3) Preview results
doctors_clean.head()
appointments_clean.head()

# --- Fix foreign key issue ---
appointments_clean = appointments_clean[
    appointments_clean["doctor_id"].isin(doctors_clean["doctor_id"])
]

cursor.execute("CREATE SCHEMA IF NOT EXISTS healthtech;")
connection.commit()

create_doctors_table = """
CREATE TABLE IF NOT EXISTS healthtech.doctors (
    doctor_id BIGINT PRIMARY KEY,
    doctor_name TEXT,
    specialty TEXT,
    ingested_at TIMESTAMPTZ
)
"""

create_appointments_table = """
CREATE TABLE IF NOT EXISTS healthtech.appointments (
    appointment_id BIGINT PRIMARY KEY,
    doctor_id BIGINT REFERENCES healthtech.doctors(doctor_id),
    patient_id BIGINT,
    appointment_date DATE,
    status TEXT,
    ingested_at TIMESTAMPTZ
)
"""

cursor.execute(create_doctors_table)
cursor.execute(create_appointments_table)
connection.commit()
print("Tables verified or created")

upsert_doctors = """
    INSERT INTO healthtech.doctors (doctor_id, doctor_name, specialty, ingested_at)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (doctor_id)
    DO UPDATE SET
        doctor_name = EXCLUDED.doctor_name,
        specialty = EXCLUDED.specialty,
        ingested_at = EXCLUDED.ingested_at
"""

upsert_appointments = """
    INSERT INTO healthtech.appointments (appointment_id, doctor_id, patient_id, appointment_date, status, ingested_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (appointment_id)
    DO UPDATE SET
        doctor_id = EXCLUDED.doctor_id,
        patient_id = EXCLUDED.patient_id,
        appointment_date = EXCLUDED.appointment_date,
        status = EXCLUDED.status,
        ingested_at = EXCLUDED.ingested_at
"""

# === 4️⃣ Prepare Data for Insert ===
doctor_records = doctors_clean[["doctor_id", "doctor_name", "specialty", "ingested_at"]].values.tolist()
appointment_records = appointments_clean[["appointment_id", "doctor_id", "patient_id", "appointment_date", "status", "ingested_at"]].values.tolist()

# === 5️⃣ Execute UPSERTs ===
print(f"Upserting {len(doctor_records)} doctors...")
execute_batch(cursor, upsert_doctors, doctor_records, page_size=100)

print(f"Upserting {len(appointment_records)} appointments...")
execute_batch(cursor, upsert_appointments, appointment_records, page_size=100)

# === 6️⃣ Commit and Close ===
connection.commit()
print("Data successfully upserted into PostgreSQL!")
