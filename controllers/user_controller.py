from fastapi import APIRouter, Depends
from auth.auth import get_current_user
from models import User
from schemas.user_schema import UserResponse

router = APIRouter(prefix="/users",tags=["Users"])

# /me endpoint is protected by token (get_current_uesr)
@router.get("/me",response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user