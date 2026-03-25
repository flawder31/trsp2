import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status, Response, Request, Depends, Header, Cookie
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from models import UserCreate, LoginRequest, Product
from auth import (
    authenticate_user, create_session_token, verify_session_token,
    validate_and_update_session, get_user_profile, USERS_DB, SESSIONS_DB
)
from products import sample_products, get_product_by_id, search_products
from headers import CommonHeaders, get_server_time, HeadersResponse, InfoResponse

app = FastAPI(
    title="FastAPI Control Work",
    description="Контрольная работа по технологиям разработки серверных приложений",
    version="1.0.0"
)


# Задание 3.1
@app.post("/create_user", response_model=UserCreate, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    return user


# Задание 3.2
@app.get("/product/{product_id}", response_model=Product)
async def get_product(product_id: int):
    product = get_product_by_id(product_id)
    return product


# Задание 3.2
@app.get("/products/search", response_model=list[Product])
async def search_products_endpoint(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 10
):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    results = search_products(keyword, category, limit)
    return results


# Задание 5.1
@app.post("/login_v1")
async def login_v1(
    response: Response,
    username: str,
    password: str
):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    session_token = str(uuid.uuid4())
    
    SESSIONS_DB[session_token] = {
        "user_id": user["user_id"],
        "username": username,
        "created_at": time.time()
    }
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=300,
        secure=False
    )
    
    return {"message": "Login successful"}


# Задание 5.1
@app.get("/user_v1")
async def get_user_v1(
    request: Request,
    response: Response,
    session_token: Optional[str] = Cookie(None)
):
    if not session_token or session_token not in SESSIONS_DB:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Unauthorized"}
    
    session = SESSIONS_DB[session_token]
    return {
        "user_id": session["user_id"],
        "username": session["username"],
        "message": "Profile information"
    }


# Задание 5.2
@app.post("/login")
async def login(
    response: Response,
    login_data: LoginRequest
):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    current_time = int(time.time())
    signed_token = create_session_token(user["user_id"], current_time)
    
    SESSIONS_DB[user["user_id"]] = {
        "user_id": user["user_id"],
        "username": login_data.username,
        "last_activity": current_time
    }
    
    response.set_cookie(
        key="session_token",
        value=signed_token,
        httponly=True,
        max_age=300,
        secure=False
    )
    
    return {"message": "Login successful", "user_id": user["user_id"]}


# Задание 5.2
@app.get("/profile")
async def get_profile(
    request: Request,
    response: Response,
    session_token: Optional[str] = Cookie(None)
):
    if not session_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Unauthorized"}
    
    user_id, timestamp = verify_session_token(session_token)
    
    if user_id is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Invalid session"}
    
    profile = get_user_profile(user_id)
    if not profile:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Unauthorized"}
    
    return {
        "user_id": profile["user_id"],
        "username": profile["username"],
        "email": profile["email"],
        "message": "Profile information"
    }


# Задание 5.3
@app.post("/login_v3")
async def login_v3(
    response: Response,
    login_data: LoginRequest
):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    current_time = int(time.time())
    user_id = user["user_id"]
    
    signed_token = create_session_token(user_id, current_time)
    
    SESSIONS_DB[user_id] = {
        "user_id": user_id,
        "username": login_data.username,
        "email": user["email"],
        "last_activity": current_time
    }
    
    response.set_cookie(
        key="session_token",
        value=signed_token,
        httponly=True,
        max_age=300,
        secure=False
    )
    
    return {"message": "Login successful", "user_id": user_id}


# Задание 5.3
@app.get("/profile_v3")
async def get_profile_v3(
    request: Request,
    response: Response,
    session_token: Optional[str] = Cookie(None)
):
    if not session_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Unauthorized"}
    
    current_time = int(time.time())
    
    user_id, new_token, should_update = validate_and_update_session(session_token, current_time)
    
    if user_id is None:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Session expired"}
    
    session_data = SESSIONS_DB.get(user_id)
    if not session_data:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Invalid session"}
    
    if should_update:
        new_signed_token = create_session_token(user_id, current_time)
        response.set_cookie(
            key="session_token",
            value=new_signed_token,
            httponly=True,
            max_age=300,
            secure=False
        )
        
        SESSIONS_DB[user_id]['last_activity'] = current_time
    
    return {
        "user_id": session_data["user_id"],
        "username": session_data["username"],
        "email": session_data["email"],
        "last_activity": datetime.fromtimestamp(SESSIONS_DB[user_id]['last_activity']).isoformat(),
        "message": "Profile information"
    }


# Задание 5.4
@app.get("/headers", response_model=HeadersResponse)
async def get_headers(
    user_agent: str = Header(..., alias="User-Agent"),
    accept_language: str = Header(..., alias="Accept-Language")
):
    return HeadersResponse(
        User_Agent=user_agent,
        Accept_Language=accept_language
    )


# Задание 5.4
@app.get("/info", response_model=InfoResponse)
async def get_info(
    response: Response,
    user_agent: str = Header(..., alias="User-Agent"),
    accept_language: str = Header(..., alias="Accept-Language")
):
    response.headers["X-Server-Time"] = get_server_time()
    
    return InfoResponse(
        message="Добро пожаловать! Ваши заголовки успешно обработаны.",
        headers={
            "User-Agent": user_agent,
            "Accept-Language": accept_language
        }
    )


@app.get("/")
async def root():
    return {
        "message": "FastAPI Control Work",
        "endpoints": [
            "POST /create_user - Create user (3.1)",
            "GET /product/{product_id} - Get product by ID (3.2)",
            "GET /products/search - Search products (3.2)",
            "POST /login - Login with signed cookie (5.2)",
            "GET /profile - Protected profile (5.2)",
            "POST /login_v3 - Login with dynamic session (5.3)",
            "GET /profile_v3 - Protected with session extension (5.3)",
            "GET /headers - Get headers (5.4)",
            "GET /info - Get headers with server time (5.4)"
        ]
    }


@app.get("/sessions")
async def list_sessions():
    return {
        "active_sessions": [
            {
                "user_id": user_id,
                "last_activity": datetime.fromtimestamp(data['last_activity']).isoformat()
            }
            for user_id, data in SESSIONS_DB.items()
        ]
    }