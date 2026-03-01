from pydantic import BaseModel
from datetime import datetime


class JobInput(BaseModel):
    Rating:float	
    Location:int	
    Size:int	
    Founded	:int
    Industry:int	
    Sector:int	
    Revenue:int	
    Competitors:int
    Company_Name:int	
    Type_ownership:int
  
class UserSignup(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str