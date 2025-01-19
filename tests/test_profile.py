from fastapi.testclient import TestClient
from .conftest import clear_db
from main import app
import pyotp
from app.authentication import User
from PIL import Image
from io import BytesIO

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


def create_test_image():
    """Creates an in-memory image for testing."""
    image = Image.new("RGB", (100, 100), color=(0, 255, 0))  # green square image
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)  # Reset the pointer to the start of the stream
    return image_bytes


def test_get_profile_unverified_user(clear_db):
    register_response = client.post("/auth/signup",json=test_user)
    user = User.find_one({"email":test_user["email"]})
    user = deserialize_user(user)
    response = client.get("/profile/"+user["username"])
    assert response.status_code == 404
    assert response.json() == {"detail": "user not found"}

# test for getting a profile
def test_get_profile(clear_db):
    # first create a new user and verify it
    register_response = client.post("/auth/signup",json=test_user)
    user = User.find_one({"email":test_user["email"]})
    user = deserialize_user(user)
    verification_code = pyotp.TOTP(user["otp_secret"],interval=600).now()
    verify_response = client.post("/auth/verify",json={"id":register_response.json()["id"],"verification_code":verification_code})
    # then get the profile
    response=client.get("/profile/"+user["username"],headers={"Authorization":f"Bearer {verify_response.json()['access_token']}"})
    assert response.status_code == 200
    assert response.json()["name"] == test_user["name"]


# test upload profile picture
def test_upload_profile_picture(clear_db):
    # first create a new user and verify it
    register_response = client.post("/auth/signup",json=test_user)
    user = User.find_one({"email":test_user["email"]})
    user = deserialize_user(user)
    verification_code = pyotp.TOTP(user["otp_secret"],interval=600).now()
    verify_response = client.post("/auth/verify",json={"id":register_response.json()["id"],"verification_code":verification_code})
    assert verify_response.status_code == 200
    # then get the profile
    test_image=create_test_image()
    files = {"picture": ("test_image.jpg", test_image, "image/jpeg")}
    upload_response = client.post("/profile/upload",files=files,headers={"Authorization":f"Bearer {verify_response.json()['access_token']}"})
    print(upload_response.json())
    assert upload_response.status_code == 200
    assert upload_response.json()["detail"] == "image uploaded"