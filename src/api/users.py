"""
User Management API Endpoints

Provides user and API key management for multi-user deployments.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from pydantic import BaseModel, EmailStr

from src.auth.user_manager import user_manager
from src.core.logging import logger

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    role: str = "user"
    quota_requests: int = 1000
    quota_tokens: int = 1000000
    quota_cost: float = 10.0


class QuotaUpdate(BaseModel):
    quota_requests: Optional[int] = None
    quota_tokens: Optional[int] = None
    quota_cost: Optional[float] = None


@router.post("/api/users")
async def create_user(user: UserCreate):
    """
    Create a new user with API key.

    Returns user details including API key (only shown once!).
    """
    try:
        result = user_manager.create_user(
            username=user.username,
            email=user.email,
            role=user.role,
            quota_requests=user.quota_requests,
            quota_tokens=user.quota_tokens,
            quota_cost=user.quota_cost
        )

        return {
            "status": "success",
            "user": result,
            "warning": "Save the API key securely - it won't be shown again!"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/users/me")
async def get_current_user(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    """
    Get current user info based on API key.
    """
    # Extract API key
    api_key = x_api_key
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]

    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    user = user_manager.validate_api_key(api_key)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Remove sensitive fields
    user_info = {
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "active": user["active"],
        "created_at": user["created_at"]
    }

    return user_info


@router.get("/api/users/me/quota")
async def get_user_quota(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    """
    Get current user's quota status.

    Returns remaining quota for requests, tokens, and cost.
    """
    # Extract API key
    api_key = x_api_key
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]

    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    user = user_manager.validate_api_key(api_key)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    quota_status = user_manager.check_user_quota(user["id"])

    if "error" in quota_status:
        raise HTTPException(status_code=500, detail=quota_status["error"])

    return quota_status


@router.get("/api/users/me/usage")
async def get_user_usage(
    days: int = 7,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    """
    Get user's usage history.

    Returns daily usage stats for the specified period.
    """
    # Extract API key
    api_key = x_api_key
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]

    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    user = user_manager.validate_api_key(api_key)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        import sqlite3
        from datetime import datetime, timedelta

        conn = sqlite3.connect(user_manager.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

        cursor.execute("""
            SELECT date, request_count, token_count, cost
            FROM user_usage
            WHERE user_id = ? AND date >= ?
            ORDER BY date DESC
        """, (user["id"], since))

        rows = cursor.fetchall()
        conn.close()

        usage_data = [dict(row) for row in rows]

        return {
            "user_id": user["id"],
            "username": user["username"],
            "period_days": days,
            "usage": usage_data
        }

    except Exception as e:
        logger.error(f"Failed to get user usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
