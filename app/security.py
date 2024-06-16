from passlib.context import CryptContext
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import os
import dotenv

dotenv.load_dotenv(".env")

password_context = CryptContext(schemes=["bcrypt"],deprecated="auto")


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