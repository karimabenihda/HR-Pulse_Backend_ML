from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv
import pandas as pd
import time

load_dotenv()

endpoint = os.getenv("endpoint") 
key = os.getenv("api_key")

df=pd.read_csv('./data/clean_jobs2.csv')

descriptions=df['Job_Description'].tolist()

def extract_skills(descriptions: list[str]) -> list[list[str]]:
    client = TextAnalyticsClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    all_skills=[]
    batch_size = 2
    
    for i in range(0,len(descriptions),batch_size):
        batch=descriptions[i:i + batch_size]  #C'est du slicing (découpage) de liste Python.
        
        batch=[
        text[:1000]          # ✅ Garder seulement les 1000 premiers caractères
        if isinstance(text, str)# 🔍 SI le texte est bien une string
        else ""              # ❌ SINON remplacer par une string vide
        for text in batch    # 🔄 Pour chaque texte dans le batch
        ]
        response = client.recognize_entities(batch)
    
        for doc in response:
            print("---- Nouvelle offre ----")
            if not doc.is_error:
                skills = list(set(
                        entity.text
                        for entity in doc.entities
                        if entity.category in ["Skill", "Product"]
                        and entity.confidence_score >= 0.80
                    ))
            
                for entity in doc.entities:
                    if entity.confidence_score >=0.80:
                        print(f"Texte : {entity.text}")
                        print(f"Type : {entity.category}")
                        print(f"Sous-type : {entity.subcategory}")
                        print(f"Score : {entity.confidence_score}")
                        print("-----")
                        
                all_skills.append(", ".join(skills))
            else:
                all_skills.append("")

        time.sleep(1.0)

    print(f"Descriptions: {len(descriptions)} | All skills: {len(all_skills)}")  # ← ici
    df["extracted_skills"] = all_skills
    df.to_csv('./data/clean_jobs_with_skills.csv', index=False)
    
extract_skills(descriptions)


