"""
Authentication routes with error handling.
"""

from fastapi import APIRouter, Depends
from auth import SignupRequest, LoginRequest, AuthResponse, signup_user, login_user, verify_token, TokenPayload

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=AuthResponse)
async def signup(signup_data: SignupRequest):
    """Register a new user account."""
    return await signup_user(signup_data)


@router.post("/login", response_model=AuthResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and generate JWT token."""
    return await login_user(login_data)


@router.get("/me")
async def get_current_user(token_payload: TokenPayload = Depends(verify_token)):
    """Get current authenticated user information."""
    return {
        "user_id": token_payload.sub,
        "email": token_payload.email
    }
