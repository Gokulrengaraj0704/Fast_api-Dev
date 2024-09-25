from fastapi import FastAPI, Form, Request, Depends, HTTPException, BackgroundTasks, UploadFile, File, Path
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, constr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeTimedSerializer
from database import SessionLocal, engine
from models import User, Event, PendingEvent, EventForm, ImageModel
from schemas import UserSchema, EventFormCreate, UserDetails, ImageCreate, ImageResponse, ImageBase
from database import Base
import smtplib
import base64
from typing import List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from jinja2 import Template
from starlette.status import HTTP_401_UNAUTHORIZED
from functools import wraps
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import json
import os
from uuid import UUID, uuid4
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="b436b7880fc6857423bb4be8")

templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

serializer = URLSafeTimedSerializer("b436b7880fc6857423bb4be8")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EmailSettings(BaseModel):
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: constr(min_length=1)
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM: EmailStr
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool


email_settings = EmailSettings(
    MAIL_USERNAME="gokulrengaraj07@gmail.com",
    MAIL_PASSWORD="nhlq zhsr kivr wslm",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM="gokulrengaraj07@gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False
)

conf = ConnectionConfig(
    MAIL_USERNAME=email_settings.MAIL_USERNAME,
    MAIL_PASSWORD=email_settings.MAIL_PASSWORD,
    MAIL_PORT=email_settings.MAIL_PORT,
    MAIL_SERVER=email_settings.MAIL_SERVER,
    MAIL_FROM=email_settings.MAIL_FROM,
    MAIL_STARTTLS=email_settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=email_settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=email_settings.USE_CREDENTIALS,
    VALIDATE_CERTS=email_settings.VALIDATE_CERTS
)

fm = FastMail(conf)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],  # Allow only your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request):
    user_email = request.session.get('user_email')
    if not user_email:
        raise HTTPException(status_code=403, detail="Not authenticated")
    return user_email


def get_current_admin(request: Request):
    admin = request.session.get('admin')
    if not admin:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return admin


def require_login(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            get_current_user(request)
            if not request.session.get('authenticated'):
                raise HTTPException(status_code=401, detail="Not authenticated")
        except HTTPException:
            return RedirectResponse(url="/login", status_code=303)
        return await func(request, *args, **kwargs)

    return wrapper


def require_admin(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            get_current_admin(request)
            if not request.session.get('authenticated'):
                raise HTTPException(status_code=401, detail="Not authenticated")
        except HTTPException:
            return RedirectResponse(url="/admin-login", status_code=303)
        return await func(request, *args, **kwargs)

    return wrapper


def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def generate_qr_code(data: dict, file_path: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(file_path)


@app.get("/", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})



class UserRegisterRequest(BaseModel):
    email: str
    password: str

@app.post("/register", response_class=JSONResponse)
async def register_post(user: UserRegisterRequest, db: Session = Depends(get_db)):
    try:
        # Check if the user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            return JSONResponse(content={"success": False, "message": "Email already exists"}, status_code=400)

        # Create a new user
        unique_user_id = uuid4()
        new_user = User(
            id=unique_user_id,
            email=user.email,
            password=user.password,
            is_restricted=False,
            create_event=True,
            create_form=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return JSONResponse(content={"success": True, "user_id": str(unique_user_id), "message": "Registration successful"}, status_code=201)

    except Exception as e:
        db.rollback()
        return JSONResponse(content={"success": False, "message": f"An error occurred: {str(e)}"}, status_code=500)
@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/user/{user_id}", response_class=JSONResponse)
async def get_user_details(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            response_data = {
                "success": True,
                "message": "User details retrieved successfully",
                "user_id": str(user.id),
                "user_email": user.email,
                "is_active": user.is_active,
                "is_restricted": user.is_restricted,
                "permissions": {
                    "create_event": user.create_event,
                    "create_form": user.create_form,
                    "view_registrations": user.view_registrations
                }
            }
            return JSONResponse(content=response_data, status_code=200)
        else:
            return JSONResponse(content={"success": False, "message": "User not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"success": False, "message": f"An error occurred: {str(e)}"}, status_code=500)


@app.post("/login", response_class=JSONResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.email == email).first()
        if user and user.password == password and user.is_active:
            # Create the response JSON
            response_data = {
                "success": True,
                "message": "Login successful",
                "user_id": str(user.id),  # Convert UUID to string
                "user_email": email,
                "is_restricted": user.is_restricted,
                "permissions": {
                    "create_event": user.create_event,
                    "create_form": user.create_form,
                    "view_registrations": user.view_registrations
                }
            }
            return JSONResponse(content=response_data, status_code=200)
        else:
            return JSONResponse(content={"success": False, "message": "Invalid credentials"}, status_code=401)
    except Exception as e:
        return JSONResponse(content={"success": False, "message": f"An error occurred: {str(e)}"}, status_code=500)
    
