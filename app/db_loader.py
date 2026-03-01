import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import json

load_dotenv()

DB_URL=os.getenv('DB_URL')

engine= create_engine(DB_URL)

with engine.connect() as connection:
    connection.execute(text("""
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='jobs'
        ) 
        CREATE TABLE jobs (
        id INT IDENTITY(1,1) PRIMARY KEY, -- Starts at 1, increments by 1
        title NVARCHAR(255),
            skills NVARCHAR(MAX)
        )
    """))
    connection.commit()
print('table created successufelly')
    
df=pd.read_csv('./data/clean_jobs_with_skills.csv')

with engine.connect() as connection :
    for _, row in df.iterrows():
        connection.execute(text("""
            INSERT INTO jobs (id,title,skills)
            VALUES (:id, :title, :skills)
        """),{
        "id":int(row["index"]),
        "title":str(row["Job_Title"]),
        "skills": str(row["extracted_skills"])
    } )
    connection.commit()

    
print(f'✅ {len(df)} offres injectées dans Azure SQL')
