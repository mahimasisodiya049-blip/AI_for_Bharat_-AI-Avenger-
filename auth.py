"""
Authentication module for KiroFeed API.
Handles user signup, login, and JWT token validation using AWS Cognito.
"""

import boto3
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from typing import Optional
import requests
from functools import lru_cache
from botocore.exceptions import NoCredentialsError, ClientError

from config import config


# Pydantic models for request/response
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class TokenPayload(BaseModel):
    sub: str  # user_id
    email: str
    exp: int


# Security scheme for JWT
security = HTTPBearer()


def get_cognito_client():
    """Get Cognito client with error handling."""
    try:
        return boto3.client(
            'cognito-idp',
            region_name=config.COGNITO_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
        )
    except NoCredentialsError:
        raise HTTPException(
            status_code=500,
            detail="AWS credentials not found. Please check your environment variables."
        )


@lru_cache()
def get_cognito_public_keys():
    """Fetch and cache Cognito public keys for JWT verification."""
    keys_url = f"https://cognito-idp.{config.COGNITO_REGION}.amazonaws.com/{config.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    try:
        response = requests.get(keys_url, timeout=10)
        response.raise_for_status()
        return response.json()['keys']
    except requests.Timeout:
        raise HTTPException(status_code=503, detail="Cognito service timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Cognito public keys: {str(e)}")


async def signup_user(signup_data: SignupRequest) -> AuthResponse:
    """Register a new user with AWS Cognito."""
    try:
        cognito_client = get_cognito_client()
        
        response = cognito_client.sign_up(
            ClientId=config.COGNITO_CLIENT_ID,
            Username=signup_data.email,
            Password=signup_data.password,
            UserAttributes=[
                {'Name': 'email', 'Value': signup_data.email},
                {'Name': 'name', 'Value': signup_data.name}
            ]
        )
        
        user_sub = response['UserSub']
        
        # Auto-confirm user for development
        try:
            cognito_client.admin_confirm_sign_up(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=signup_data.email
            )
        except Exception:
            pass
        
        # Authenticate to get tokens
        auth_response = cognito_client.initiate_auth(
            ClientId=config.COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': signup_data.email,
                'PASSWORD': signup_data.password
            }
        )
        
        access_token = auth_response['AuthenticationResult']['AccessToken']
        
        return AuthResponse(
            access_token=access_token,
            user_id=user_sub,
            email=signup_data.email
        )
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if 'UsernameExists' in error_code:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        elif 'InvalidPassword' in error_code:
            raise HTTPException(status_code=400, detail="Password does not meet requirements")
        else:
            raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


async def login_user(login_data: LoginRequest) -> AuthResponse:
    """Authenticate user and generate JWT token."""
    try:
        cognito_client = get_cognito_client()
        
        response = cognito_client.initiate_auth(
            ClientId=config.COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': login_data.email,
                'PASSWORD': login_data.password
            }
        )
        
        access_token = response['AuthenticationResult']['AccessToken']
        decoded = jwt.get_unverified_claims(access_token)
        user_id = decoded.get('sub')
        email = decoded.get('email', login_data.email)
        
        return AuthResponse(
            access_token=access_token,
            user_id=user_id,
            email=email
        )
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if 'NotAuthorized' in error_code or 'UserNotFound' in error_code:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        else:
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> TokenPayload:
    """Middleware to validate JWT token from request headers."""
    token = credentials.credentials
    
    try:
        cognito_client = get_cognito_client()
        
        # Validate token with Cognito
        try:
            cognito_client.get_user(AccessToken=token)
        except ClientError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        # Decode token
        decoded = jwt.get_unverified_claims(token)
        user_id = decoded.get('sub')
        email = decoded.get('email', '')
        exp = decoded.get('exp', 0)
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        return TokenPayload(sub=user_id, email=email, exp=exp)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")
