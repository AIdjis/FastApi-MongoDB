from fastapi import APIRouter,status,HTTPException,Response,UploadFile,File,Form,Request,Depends,BackgroundTasks
from app.database import client
from fastapi.responses import JSONResponse
from app.schemas import CreateUser,LoginUser,ResponseUser
from bson import ObjectId
from typing import List
from datetime import datetime
from .security import get_password_hash,verify_password,send_email
import pyotp


# create the user collection
User=client.MarketPlace.users

auth_router=APIRouter(prefix="/auth",tags=["Authentication"])



@auth_router.post("/signup",status_code=status.HTTP_201_CREATED,response_model=ResponseUser)
def signup(body:CreateUser,background_tasks:BackgroundTasks):
    if User.find_one({"email":body.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="email already exist")
    body.password=get_password_hash(body.password)
    valid_user=dict(body)
    valid_user["create_at"]=datetime.now()
    valid_user["is_active"]=False
    otp_base32 = pyotp.random_base32()
    totp = pyotp.TOTP(otp_base32,interval=600)
    verification_code=totp.now()
    background_tasks.add_task(send_email,body.email,verification_code)
    valid_user["otp_secret"]=otp_base32
    new_user=User.insert_one(valid_user)
    response={"id":str(new_user.inserted_id),"email":body.email}

    return response
