from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
import joblib
import pandas as pd
from pydantic import BaseModel
import os
from app.schemas import JobInput,UserSignup, Token, UserLogin
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from jose import jwt
from sqlalchemy.orm import Session
from app.models import User,Base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from uuid import uuid4
from fastapi import Depends, Header
from jose import JWTError, jwt

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from tracing import setup_tracing

app = FastAPI(title="HR-Pulse API")

tracer = setup_tracing()

FastAPIInstrumentor().instrument_app(app)


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # convert to int

DB_URL=os.getenv('DB_URL')

engine = create_engine(
    DB_URL,
    pool_pre_ping=True,  # Vérifie si la connexion est vivante avant de l'utiliser
    pool_recycle=1800,   # Recrée les connexions toutes les 30 minutes
)

Base.metadata.create_all(bind=engine)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "modelrf.pkl")

# Chargement
model = joblib.load(MODEL_PATH)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


origins = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,     
    allow_methods=["*"],        
    allow_headers=["*"],         
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()





def get_current_user(authorization: str = Header(None)):
    """
    Vérifie que le token JWT est valide et retourne l'email de l'utilisateur.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token manquant")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Token invalide")
    except ValueError:
        raise HTTPException(status_code=401, detail="Format d'autorisation invalide")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")



def create_access_token(data: dict, expires_delta: int = None):
    """Génère un JWT pour ton application"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta or ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ----- Login -----

@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    # 1. Requête SQL
    query = text("SELECT email, password FROM users WHERE email = :email")
    
    try:
        # On exécute la requête
        result = db.execute(query, {"email": user.email}).fetchone()
        
        if not result:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")

        # Récupération des données SQL
        db_email = result[0]
        db_password = result[1]  # C'est le mot de passe stocké en clair dans Azure SQL

        if user.password.strip() != db_password.strip():
            raise HTTPException(status_code=401, detail="Mot de passe incorrect")

        # 3. Création du Token
        token = create_access_token(data={"sub": db_email})
        
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException as e:
        raise e 
    except Exception as e:
        # Affiche l'erreur précise dans ton terminal uvicorn
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}") 
    
    
@app.post("/signup", response_model=Token)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    try:
        # Check if user exists
        check_query = text("SELECT COUNT(*) FROM users WHERE email = :email")
        count = db.execute(check_query, {"email": user_data.email}).scalar()
        
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cet email existe déjà"
            )
        
        # Validate
        if not user_data.firstname.strip() or not user_data.lastname.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le prénom et le nom sont obligatoires"
            )
        
        if len(user_data.password.strip()) < 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le mot de passe doit contenir au moins 4 caractères"
            )
        
        # Insert user
        insert_query = text("""
            INSERT INTO users (email, password, firstname, lastname, created_at)
            VALUES (:email, :password, :firstname, :lastname, :created_at)
        """)
        
        db.execute(insert_query, {
            "email": user_data.email.lower(),
            "password": user_data.password,
            "firstname": user_data.firstname.strip(),
            "lastname": user_data.lastname.strip(),
            "created_at": datetime.utcnow()
        })
        
        db.commit()
        
        # Get user
        get_user_query = text("""
            SELECT id, email, firstname, lastname
            FROM users 
            WHERE email = :email
        """)
        
        result = db.execute(get_user_query, {"email": user_data.email.lower()}).fetchone()
        user_id, db_email, firstname, lastname = result
        
        # Create token
        token = create_access_token({"sub": db_email, "user_id": user_id})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": db_email,
                "firstname": firstname,
                "lastname": lastname
            }
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Signup error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'inscription"
        )
        
        
    
@app.post("/predict")
def predict_salary(data: JobInput,user_email: str = Depends(get_current_user)):
    df = pd.DataFrame([data.dict()])
    prediction = model.predict(df)
    return {"estimated_salary": prediction[0]}



@app.get("/jobs")
def get_jobs(user_email: str = Depends(get_current_user)):
    query = "SELECT * FROM jobs" 
    df = pd.read_sql(query, engine)
    return df.to_dict(orient="records")


@app.get("/job_list")
def get_jobs(user_email: str = Depends(get_current_user)):
    query = "SELECT TOP 3 * FROM job" 
    df = pd.read_sql(query, engine)
    return df.to_dict(orient="records")

@app.get("/compute")
def compute():
    with tracer.start_as_current_span("manual-span"):
        result = sum(x for x in range(1000000))
        return {"sum": result}