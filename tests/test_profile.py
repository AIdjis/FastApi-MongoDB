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
            "picture":user["picture"],
            "email":user["email"]
    }


def test_get_profile_unverified_user(clear_db):
    register_response = client.post("/auth/signup",json=test_user)
    user = User.find_one({"email":test_user["email"]})
    user = deserialize_user(user)
    response = client.get("/profile/"+user["username"])
    assert response.status_code == 404
    assert response.json() == {"detail": "user not found"}