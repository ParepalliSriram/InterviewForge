import bcrypt
from fastapi import Request, HTTPException, status

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

async def get_current_user_id(request: Request) -> str | None:
    """Returns the current user's ID from session if authenticated, else None."""
    return request.session.get("user_id")

async def require_user_id(request: Request) -> str:
    """Enforces authentication and returns the user's ID. Raises HTTP 401 if unauthenticated."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or not authenticated. Please log in."
        )
    return user_id
