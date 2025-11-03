## Pipeline Structure

```
Pipeline/
│
├── ingest_data.py            # Extracts Excel data
├── transformation_data.py    # Cleans and transforms the datasets
├── load_data.py              # Loads cleaned data into PostgreSQL
├── datasets/                 # Folder containing Excel input files
│   ├── Data Enginner Doctors Excel - VIP Medical Group.xlsx
│   └── Data Engineer Appointments Excel - VIP Medical Group.xlsx
│
├── output/                   # Folder for transformed CSVs before uploading into postgresql
└── logs/                     # Folder for logs
```

---

## Setup Instructions

```bash
git clone https://github.com/<your-username>/HealthTech-ETL.git
```

```bash
cd HealthTech-ETL/Pipeline
```

---

### Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate 
venv\Scripts\activate   
```

---

### Install dependencies

```bash
pip install pandas psycopg2-binary openpyxl numpy
```

---

### Set up PostgreSQL

```sql
CREATE DATABASE healthtech_db;
```

```python

##Update the credentials.json file based on the details below, and make sure to include the new password or updated credentials

connection = psycopg2.connect(
    host='localhost',
    user='postgres',
    password='123',          # <-- Replace with your password
    database='healthtech_db'
)
```

---

### Run the pipeline

```bash
python ingest_data.py
python transformation_data.py
python load_data.py
```

---

## ETL Breakdown

### Extract (`ingest_data.py`)

**Purpose:**  
Reads the raw Excel files containing doctors and appointments information.

**Process:**
- Loads both Excel files using `pandas.read_excel()` with the `openpyxl` engine.  
- Logs every major event (start, file path, row count, completion) in both console and `logs/ingest.log`.  
- Returns two DataFrames:
  - `doctors_df`: Basic information about doctors.  
  - `appointments_df`: Appointment details including patient, doctor, and status.  

---

### Transform (`transformation_data.py`)

**Purpose:**  
Cleans, standardizes, and prepares the data for loading.

**Key Steps:**

#### a) Normalization
- Converts column names to lowercase.  
- Replaces spaces and symbols with underscores for consistency.  

#### b) Doctors Transformation (`transform_doctors`)
- Renames columns (`name → doctor_name`, `specialty` kept as-is).  
- Removes duplicates based on `doctor_id`.  
- Strips whitespace from text fields.  
- Adds `ingested_at` timestamp to track load time.  

#### c) Appointments Transformation (`transform_appointments`)
- Standardizes all column names and data types.  
- Renames fields (`booking_id → appointment_id`, `doctorid → doctor_id`, etc.).  
- Cleans non-numeric IDs and converts them to integers.  
- Normalizes `appointment_date` to `YYYY-MM-DD` format.  
- Fixes invalid years (e.g., anything >2025 is capped at 2025).  
- Converts all status values to lowercase and replaces `"canceled"` → `"cancelled"`.  
- Adds an `ingested_at` timestamp for data lineage.  

#### d) Output
- Produces two cleaned DataFrames:
  - `doctors_clean`
  - `appointments_clean`  
- Optionally saves them as CSVs under `/output/` for manual inspection.  

---

### Load (`load_data.py`)

**Purpose:**  
Loads the cleaned data into PostgreSQL under the `healthtech` schema.

**Key Steps:**
- **Database Connection:** Connects to PostgreSQL using `psycopg2`.  
- **Schema & Table Setup:**
  - Creates `healthtech.doctors` and `healthtech.appointments` tables if they don’t exist.  
  - Enforces foreign key relationship between `appointments.doctor_id` and `doctors.doctor_id`.  
- **Upsert Logic:**  
  Uses `ON CONFLICT` to update existing rows (avoiding duplicates).  
- **Batch Inserts:**  
  Inserts data efficiently with `execute_batch()` for high performance.  
- **Validation:**  
  Logs and prints successful upserts for both datasets.  

---

## Recommended AWS Architecture

| Component | AWS Service | Purpose |
|------------|--------------|----------|
| **Extract** | Amazon S3 | Store raw Excel files |
| **Orchestration** | AWS Step Functions | Coordinate ETL steps |
| **Transform** | AWS Glue | Data cleaning and transformation |
| **Load** | Amazon RDS (PostgreSQL) | Store processed data |

