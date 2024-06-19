from fastapi import APIRouter,status,HTTPException,Response,UploadFile,File,Form,Request,Depends,BackgroundTasks
from app.database import client
from fastapi.responses import JSONResponse
from app.schemas import CreateUser,LoginUser,ResponseUser,Verification
from bson import ObjectId
from typing import List
from datetime import datetime
from .security import get_password_hash,verify_password,send_email,create_jwt_token
import pyotp
from datetime import timedelta


# create the user collection
User=client.MarketPlace.users

auth_router=APIRouter(prefix="/auth",tags=["Authentication"])

# setting the default access and refresh token expires time 
ACCESS_TOKEN_EXPIRES_IN:timedelta = timedelta(hours=1)
REFRESH_TOKEN_EXPIRES_IN:timedelta = timedelta(days=30)

def deserialize_data(user):
    return {"id":str(user["_id"]),
            "name":user["name"],
            "username":user["username"],
            "is_active":user["is_active"],
            "otp_secret":user["otp_secret"],
            "email":user["email"]}


@auth_router.post("/signup",status_code=status.HTTP_201_CREATED,response_model=ResponseUser)
async def signup(body:CreateUser,background_tasks:BackgroundTasks):
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


@auth_router.post("/verify",status_code=status.HTTP_200_OK)
async def verify(body:Verification,response:Response):
    user=User.find_one({"_id":ObjectId(body.id)})
    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    user_data=deserialize_data(user)
    otp_base32=user_data["otp_secret"]
    totp = pyotp.TOTP(otp_base32,interval=600)

    # verifying if the verification code is correct
    if not totp.verify(body.verification_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='please enter a correct verification code')
    
    User.update_one({"_id":ObjectId(body.id)},{"$set":{"is_active":True}})

    # generating access and refresh token and storing them in cookies
    access_token= await create_jwt_token(data={"id":user_data["id"]},expires_time=ACCESS_TOKEN_EXPIRES_IN,mode="access_token")
    refresh_token= await create_jwt_token(data={"id":user_data["id"]},expires_time=REFRESH_TOKEN_EXPIRES_IN,mode="refresh_token")

    response.set_cookie(key="access_token",value=access_token,expires=ACCESS_TOKEN_EXPIRES_IN,httponly=True,
                       domain=None,max_age=ACCESS_TOKEN_EXPIRES_IN,secure=False,samesite="lax")
    
    response.set_cookie(key="refresh_token",value=refresh_token,expires=REFRESH_TOKEN_EXPIRES_IN,httponly=True, domain=None,
                        max_age=REFRESH_TOKEN_EXPIRES_IN,secure=False,samesite="lax")
    
    response.set_cookie(key="logged_in",value="True",expires=ACCESS_TOKEN_EXPIRES_IN,domain=None,
                       max_age=ACCESS_TOKEN_EXPIRES_IN ,secure=False,httponly=False,samesite="lax")

    return {"id":user_data["id"],"type":"Bearer","access_token":access_token,"refresh_token":refresh_token} 


