from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from models import User
from schemas.user_schema import UserCreate, UserResponse, UserLogin, TokenResponse
from auth.auth import get_password_hash, verify_password, create_access_token

# Authentication router
router = APIRouter(prefix="/auth",tags=["Authentication"])

# Register Endpoint
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # check if email already exists
    existing_user = db.query(User).filter(User.email==user_data.email).first()
    # check if email is already registered
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    # creating user with input data
    new_user = User(email=user_data.email, password_hash=hashed_password)
    # save user in database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Login Endpoint
@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
def login(user_data: UserLogin, db: Session = Depends(get_db)):

    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    # checking email before password so verify_password doesn't crash
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email"
        )
    # checking password
    password_verified = verify_password(user_data.password,user.password_hash)
    if not password_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    # creating jwt token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}