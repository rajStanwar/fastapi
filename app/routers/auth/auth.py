from typing import Annotated
from fastapi import Depends
import httpx
import hashlib
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from app.utils.config import settings
from .models import OauthToken, OauthException
from app.utils.db import db
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter()
security = HTTPBearer()


@router.get(
    "/callback", 
    response_model=OauthToken, 
    responses={
        400: {"description": "Oauth Error", "model": OauthException},
    },
)
async def oauth_callback(code: str = Query(description="Authorization code")) -> OauthToken:
    """Callback to get access token for user

    Args:
        code (str, optional): Github Oauth Integration Callback.
        Defaults to Query(description="Authorization code").

    Returns:
        OauthToken: Github Oauth Access Token
    """
    async with httpx.AsyncClient() as client:
        token_result  = await client.post(
            "https://github.com/login/oauth/access_token",
            params={
                "client_id": settings.client_id,
                "client_secret": settings.client_secret,
                "code": code,
                "redirect_uri": "http://localhost:8000/v1/auth/callback",
            },
            headers={"Accept": "application/json"},
        )
        if token_result .status_code != 200:
            raise OauthException(detail=token_result .text)
        
        data = token_result.json()
        print(data)
        error = data.get("error")
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"{data.get('error')}: {data.get('error_description')}",
            )
        
        access_token: str = data.get("access_token")
        
        user_result = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        user_data = user_result.json()
        user = user_data.get("login")
        
        await db.tokens.insert_one(
            {
                "user": user,
                "access_token_hash": hashlib.sha256(access_token.encode()).hexdigest(),
                "created_date": datetime.utcnow(),
            }
        )
        return OauthToken(access_token=access_token)


async def validate_access_token(
    access_token: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """
    Validate Access token
    Returns the username or raises a 401 HTTPException

    Args:
        access_token (Annotated[HTTPAuthorizationCredentials, Depends): access token for validation

    Returns:
        str: username
    """
    print("Access token: ", access_token)
    access_token_hash = hashlib.sha256(access_token.credentials.encode()).hexdigest()
    cached_token = await db.tokens.find_one({"access_token_hash": access_token_hash})
    
    if cached_token:
        user: str | None = cached_token.get("user", None)
        if user:
            return user
    
    async with httpx.AsyncClient() as client:
        user_result = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token.credentials}"}
        )
        if user_result.status_code == 200:
            user_data = user_result.json()
            user = user_data.get("login", None)
            if user:
                await db.tokens.insert_one(
                    {
                        "user": user,
                        "access_token_hash": access_token_hash,
                        "created_date": datetime.utcnow(),
                    },
                )
                return user
            
    raise HTTPException(
        status_code=401,
        detail="Unauthorized",
    )