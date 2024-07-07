from fastapi import APIRouter,status,HTTPException,Response,Depends,BackgroundTasks
from app.database import client
from fastapi.responses import JSONResponse
from app.schemas import CreateUser,LoginUser,ResponseUser,Verification,ResendCode,ForgotPassword
from bson import ObjectId
from datetime import datetime
from .security import get_password_hash,verify_password,send_email,create_jwt_token,verify_jwt_refresh_token
import pyotp
from datetime import timedelta
import re


# create the user collection
User=client.MarketPlace.users

# the valid username of the user (only alphabets and numbers  and (.)(-) between the chracters) 
username_regex = re.compile(r"^(([a-zA-Z0-9]+)|([a-zA-Z0-9]+\.*[a-zA-Z0-9]+)|([a-zA-Z0-9]+-*[a-zA-Z0-9]+))$")


auth_router=APIRouter(prefix="/auth",tags=["Authentication"])

# setting the default access and refresh token expires time 
ACCESS_TOKEN_EXPIRES_IN:timedelta = timedelta(hours=1)
REFRESH_TOKEN_EXPIRES_IN:timedelta = timedelta(days=30)

def deserialize_data(user):
    return {"id":str(user["_id"]),
            "name":user["name"],
            "password":user["password"],
            "username":user["username"],
            "is_active":user["is_active"],
            "is_verified":user["is_verified"],
            "otp_secret":user["otp_secret"],
            "email":user["email"]}


@auth_router.post("/signup",status_code=status.HTTP_201_CREATED,response_model=ResponseUser)
async def signup(body:CreateUser,background_tasks:BackgroundTasks):
    # checking if the user email exists
    if User.find_one({"email":body.email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="email already exist")
    if User.find_one({"username":body.username}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username already taken")
    if not username_regex.match(body.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="invalid username")
    # hashing the password
    body.password=get_password_hash(body.password)
    valid_user=dict(body)
    valid_user["create_at"]=datetime.now()
    valid_user["is_active"]=True
    valid_user["is_verified"]=False

    # generating the on otp code and sending it via email
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
    # checking if the user is already verified using for password reset
    if user_data["is_verified"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="user already verified")
    
    User.update_one({"_id":ObjectId(body.id)},{"$set":{"is_verified":True}})

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


@auth_router.post("/login",status_code=status.HTTP_200_OK)
async def login(body:LoginUser,response:Response):
    user=User.find_one({"email":body.email})
    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    user_data=deserialize_data(user)
    # checking if the user is active or verified
    if not user_data["is_verified"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="user not verified")
    # checking if the password is correct
    if not verify_password(body.password,user_data["password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="invalid password")
    
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

# resent the verification code
@auth_router.post("/send-code",status_code=status.HTTP_200_OK)
async def forgot_password(body:ResendCode,background_tasks:BackgroundTasks):
    user=User.find_one({"email":body.email})
    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    user_data=deserialize_data(user)
    # generating the verification code
    otp_base32 = pyotp.random_base32()
    totp = pyotp.TOTP(otp_base32,interval=600)
    verification_code=totp.now()
    User.update_one({"_id":ObjectId(user_data["id"])},{"$set":{"otp_secret":otp_base32}})
    # sending the verification code via email
    background_tasks=BackgroundTasks()
    background_tasks.add_task(send_email,body.email,verification_code)
    return {"message":"verification code sent to your email"}

# resetting the password user 
@auth_router.patch("/forgot-password",status_code=status.HTTP_200_OK)
async def reset_password(response:Response,body:ForgotPassword):
    user=User.find_one({"email":body.email})
    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    # updating the user password
    body.password=get_password_hash(body.password)
    user_mapped=User.update_one({"email":body.email},{"$set":{"password":body.password}})
    user_data=deserialize_data(user_mapped)

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

# refreshing the access token via refresh token
@auth_router.get("/refresh-token",status_code=status.HTTP_200_OK)
async def refresh_token(response:Response,Authorize:dict=Depends(verify_jwt_refresh_token)):

    user= User.find_one({"_id":ObjectId(Authorize["id"])})

    # checking if the user exists
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='The user belonging to this token no logger exist')
    user_data=deserialize_data(user)
    access_token= await create_jwt_token(data={"id":user_data["id"]},expires_time=ACCESS_TOKEN_EXPIRES_IN,mode="access_token")  
    refresh_token= await create_jwt_token(data={"id":user_data["id"]},expires_time=REFRESH_TOKEN_EXPIRES_IN,mode="refresh_token")

    response.set_cookie(key="access_token",value=access_token,expires=ACCESS_TOKEN_EXPIRES_IN,httponly=True,
                       domain=None,max_age=ACCESS_TOKEN_EXPIRES_IN,secure=False,samesite="lax")
    
    response.set_cookie(key="refresh_token",value=refresh_token,expires=REFRESH_TOKEN_EXPIRES_IN,httponly=True, domain=None,
                        max_age=REFRESH_TOKEN_EXPIRES_IN,secure=False,samesite="lax")

    response.set_cookie(key="logged_in",value="True",expires=ACCESS_TOKEN_EXPIRES_IN,domain=None,
                       max_age=ACCESS_TOKEN_EXPIRES_IN ,secure=False,httponly=False,samesite="lax")
    
    return {"type":"Bearer","access_token":access_token,"refresh_token":refresh_token}
    









