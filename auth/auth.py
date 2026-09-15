import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models.user import User

# load environment variables from .env
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","30"))

# configuring bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"])
# extracting Bearer token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_password_hash(password: str):
    return pwd_context.hash(password) # hashed password

def verify_password(plain_password: str, hashed_password: str):
    # verified password
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy() # Copy the payload to not modify the original
    # token expiry
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    # sign the token by secret_key and create it
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    
""" Validate jwt token and return the authenticated user. """
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    auth_error  = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate User"
        )
    
    try:
        # decode the token
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        email = payload.get("sub") # extracting the email from sub in payload
        if email is None:
            raise auth_error 
    except JWTError:
        raise auth_error
    # find the user in database 
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise auth_error 
    return user