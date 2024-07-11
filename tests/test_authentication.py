from fastapi.testclient import TestClient
from .conftest import clear_db
from main import app
import pyotp
from app.authentication import User


client = TestClient(app)


test_user = {
    "email": "example@gmail.com",
    "username": "testuser",
    "name": "username",
    "password": "12345678",
}

def deserialize_user(user):
    return {"id":str(user["_id"]),
            "name":user["name"],
            "password":user["password"],
            "username":user["username"],
            "is_active":user["is_active"],
            "is_verified":user["is_verified"],
            "otp_secret":user["otp_secret"],
            "email":user["email"]}

def test_signup(clear_db):
    response = client.post("/auth/signup",json=test_user)
    assert response.status_code == 201
    assert response.json()["email"] == test_user["email"]
   

def test_singup_email_already_exist(clear_db):
    client.post("/auth/signup",json=test_user)
    response = client.post("/auth/signup",json=test_user)
    assert response.status_code == 409
    assert response.json() == {"detail": "email already exist"}
   
def test_singup_username_already_exist(clear_db):
    client.post("/auth/signup",json=test_user)
    response = client.post("/auth/signup",json={"email":"example2@gmail.com","username":"testuser","name":"username","password":"12345678"})
    assert response.status_code == 409
    assert response.json() == {"detail": "username already taken"}

# test for invalid username format (only alphabets and numbers  and (.)(-) between the chracters)
def test_singup_username_invalid(clear_db):
    response = client.post("/auth/signup",json={"email":"example@gmail.com","username":"test.","name":"username","password":"12345678"})
    assert response.status_code == 400
    assert response.json() == {"detail": "invalid username"}

# test for invalid email
def test_signup_user_invalid_email(clear_db):
    response = client.post("/auth/signup",json={"email":"test","username":"test","name":"test","password":"12345678"})
    assert response.status_code == 422
    print(response)
    assert response.json() ==  {
        'detail': [
            {
                'ctx': {
                    'reason': 'The email address is not valid. It must have exactly one '
                    '@-sign.',
                },
              'input': 'userexample.com',
              'input': 'test',
                'loc': [
                    'body',
                    'email',
                ],
                'msg': 'value is not a valid email address: The email address is not '
                'valid. It must have exactly one @-sign.',
                'type': 'value_error',
            },
        ],
    }

def test_verify_email(clear_db):
    register_response = client.post("/auth/signup",json=test_user)
    user = User.find_one({"email":test_user["email"]})
    user = deserialize_user(user)
    verification_code = pyotp.TOTP(user["otp_secret"],interval=600).now()
    response = client.post("/auth/verify",json={"id":register_response.json()["id"],"verification_code":verification_code})
    assert response.status_code == 200
    assert response.json()["id"] == register_response.json()["id"]

def test_verify_email_invalid_code(clear_db):
    register_response =client.post("/auth/signup",json=test_user)
    response = client.post("/auth/verify",json={"id":register_response.json()["id"],"verification_code":"12345"})
    assert response.status_code == 400
    assert response.json() == {"detail": "please enter a correct verification code"}   


def test_login_not_exist(clear_db):
    response = client.post("/auth/login",json={"email":"example@gmail.com","password":"12345678"})
    assert response.status_code == 404
    assert response.json() == {"detail": "user not found"}
   