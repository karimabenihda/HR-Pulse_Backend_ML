import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import json

# Load .env
load_dotenv()
DB_URL = os.getenv("DB_URL")

engine = create_engine(DB_URL)

# ==============================
# 1️⃣ CREATE TABLE IF NOT EXISTS
# ==============================

with engine.connect() as connection:
    connection.execute(text("""
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='job' AND xtype='U'
        )
        CREATE TABLE job (
            id INT IDENTITY(1,1) PRIMARY KEY,
            job_index INT,
            Rating FLOAT,
            Location NVARCHAR(255),
            Size NVARCHAR(255),
            Founded INT,
            Industry NVARCHAR(255),
            Sector NVARCHAR(255),
            Revenue NVARCHAR(255),
            Competitors NVARCHAR(MAX),
            Salary_Estimate NVARCHAR(255),
            Company_Name NVARCHAR(255),
            Type_ownership NVARCHAR(255),
            Job_Title NVARCHAR(255),
            Job_Description NVARCHAR(MAX),
            extracted_skills NVARCHAR(MAX)
        )
    """))
    connection.commit()

print("✅ Table created successfully")

# ==============================
# 2️⃣ READ CSV
# ==============================

df = pd.read_csv("./data/clean_jobs_with_skills.csv")

# ==============================
# 3️⃣ INSERT DATA
# ==============================

with engine.connect() as connection:
    for _, row in df.iterrows():
        
        # Convert skills to JSON string if needed
        skills = row["extracted_skills"]

        if pd.isna(skills):
            skills = None
        else:
            skills = str(skills)

        connection.execute(text("""
            INSERT INTO job (
                job_index,
                Rating,
                Location,
                Size,
                Founded,
                Industry,
                Sector,
                Revenue,
                Competitors,
                Salary_Estimate,
                Company_Name,
                Type_ownership,
                Job_Title,
                Job_Description,
                extracted_skills
            )
            VALUES (
                :job_index,
                :Rating,
                :Location,
                :Size,
                :Founded,
                :Industry,
                :Sector,
                :Revenue,
                :Competitors,
                :Salary_Estimate,
                :Company_Name,
                :Type_ownership,
                :Job_Title,
                :Job_Description,
                :extracted_skills
            )
        """), {
            "job_index": int(row["index"]) if not pd.isna(row["index"]) else None,
            "Rating": float(row["Rating"]) if not pd.isna(row["Rating"]) else None,
            "Location": str(row["Location"]),
            "Size": str(row["Size"]),
            "Founded": int(row["Founded"]) if not pd.isna(row["Founded"]) else None,
            "Industry": str(row["Industry"]),
            "Sector": str(row["Sector"]),
            "Revenue": str(row["Revenue"]),
            "Competitors": str(row["Competitors"]),
            "Salary_Estimate": str(row["Salary_Estimate"]),
            "Company_Name": str(row["Company_Name"]),
            "Type_ownership": str(row["Type_ownership"]),
            "Job_Title": str(row["Job_Title"]),
            "Job_Description": str(row["Job_Description"]),
            "extracted_skills": skills
        })

    connection.commit()

print(f"✅ {len(df)} offres injectées dans Azure SQL avec succès")