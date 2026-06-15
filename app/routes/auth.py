from fastapi import APIRouter, Depends, Request, HTTPException, status
from datetime import datetime
from bson import ObjectId
from app.database import get_db
from app.auth import hash_password, verify_password
from app.models import UserRegister, UserLogin, UserResponse, UserUpdateUsername

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(payload: UserRegister, db=Depends(get_db)):
    # Check if username or email already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"username": payload.username},
            {"email": payload.email.lower()}
        ]
    })
    if existing_user:
        if existing_user.get("username") == payload.username:
            raise HTTPException(status_code=400, detail="Username is already taken.")
        else:
            raise HTTPException(status_code=400, detail="Email is already registered.")

    new_user = {
        "username": payload.username,
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "created_at": datetime.utcnow()
    }
    result = await db.users.insert_one(new_user)
    
    # Create the corresponding analytics document
    await db.analytics.insert_one({
        "user_id": result.inserted_id,
        "topic_stats": {}
    })

    return UserResponse(
        id=str(result.inserted_id),
        username=new_user["username"],
        email=new_user["email"],
        created_at=new_user["created_at"]
    )

@router.post("/login")
async def login(payload: UserLogin, request: Request, db=Depends(get_db)):
    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    
    # Store user_id as string in Starlette session cookie
    request.session["user_id"] = str(user["_id"])
    request.session["username"] = user["username"]
    
    return {
        "message": "Login successful",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
    }

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_me(request: Request, db=Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"authenticated": False, "user": None}
    
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            request.session.clear()
            return {"authenticated": False, "user": None}
            
        return {
            "authenticated": True,
            "user": {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"]
            }
        }
    except Exception:
        request.session.clear()
        return {"authenticated": False, "user": None}

@router.post("/update-username")
async def update_username(payload: UserUpdateUsername, request: Request, db=Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Check if username is already taken by another user
    existing_user = await db.users.find_one({"username": payload.username})
    if existing_user and str(existing_user["_id"]) != user_id:
        raise HTTPException(status_code=400, detail="Username is already taken.")
    
    # Update the username in db
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"username": payload.username}}
    )
    
    # Update username in session
    request.session["username"] = payload.username
    
    return {"message": "Username updated successfully", "username": payload.username}
