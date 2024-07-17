from passlib.context import CryptContext
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi import Depends,HTTPException,status
from jwt.exceptions import PyJWTError,ExpiredSignatureError
from fastapi.security import OAuth2PasswordBearer
import os
import dotenv
from jwt import encode,decode
from datetime import datetime

dotenv.load_dotenv(".env")

password_context = CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


"""
in the .env file we have stored the mail credentials:
MAIL_USERNAME = YOUR MAIL
MAIL_PASSWORD = YOUR MAIL PASSWORD
"""
# print(os.getenv('MAIL_USERNAME'))
# configuring the mail
conf=ConnectionConfig(
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
    MAIL_FROM = os.getenv('MAIL_USERNAME'),
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
)



# hashing password
def get_password_hash(password):
    return password_context.hash(password)

# verifying if the password is correct
def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


# asychronously function for sending email
async  def send_email(email_conf:str,verifcation_code:str):
    fm=FastMail(config=conf)
    message = MessageSchema(
        subject="your verification code",
        recipients=[email_conf],
        body='your verification code is : '+verifcation_code,
        subtype=MessageType.plain)
    await fm.send_message(message)

# creating jwt token 
"""
in the .env file we have stored the secret key:
SECRET_KEY = YOUR SECRET KEY
"""
async def create_jwt_token(data:dict,expires_time:datetime,mode:str):
    data["exp"] = datetime.utcnow() + expires_time
    data["mode"] = mode
    encoded_jwt = encode(algorithm="HS256",key=os.getenv('SECRET_KEY'),payload=data)
    return encoded_jwt

async def verify_jwt_refresh_token(token:str=Depends(oauth_2_scheme))->dict:
    # verifying if the refresh token is valid
    try:
        payload=decode(token,os.getenv('SECRET_KEY'),algorithms=["HS256"])
        if "id" not in payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="invalid token")
        if payload["mode"] != "refresh_token":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="invalid token")
        return payload
    except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="token expired")
    except PyJWTError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="invalid token")


async def jwt_required(token:str=Depends(oauth_2_scheme))->dict:
    # verifying if the access token is valid
    try:
        payload=decode(token,os.getenv('SECRET_KEY'),algorithms=["HS256"])
        if "id" not in payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="invalid token")
        if payload["mode"] != "access_token":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="invalid token")
        return payload
    except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="token expired")
    except PyJWTError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="invalid token")

 
       
