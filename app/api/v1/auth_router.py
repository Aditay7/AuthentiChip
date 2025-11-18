from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.client import get_database
from app.models.user import UserCreate, UserLogin, UserOut
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, service: AuthService = Depends(get_auth_service)) -> UserOut:
    try:
        return await service.signup(user_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/login")
async def login(user_in: UserLogin, service: AuthService = Depends(get_auth_service)):
    try:
        return await service.login(user_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

