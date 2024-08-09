from fastapi.testclient import TestClient
from main import app
from .conftest import clear_db
import pyotp
from app.authentication import User

client = TestClient(app)

# test user example
test_user = {
    "email": "example@gmail.com",
    "username": "testuser",
    "name": "username",
    "password": "12345678",
}

# function to deserialize the user data from the database
def deserialize_user(user)-> dict:
    return {"id":str(user["_id"]),
            "name":user["name"],
            "password":user["password"],
            "username":user["username"],
            "is_active":user["is_active"],
            "is_verified":user["is_verified"],
            "otp_secret":user["otp_secret"],
            "email":user["email"]}


# test product example 
test_product = {
    "name":"test",
    "description":"test",
    "price":100,
    "currency":"USD",
    "category":"test",
    "location":"test",
    "condition":"good",
}


# test for getting all products
def test_read_items(clear_db):
    response = client.get("/product")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_read_single_item(clear_db):
    # first create a new user and verify it
    register_response = client.post("/auth/signup",json=test_user)
    user = User.find_one({"email":test_user["email"]})
    user = deserialize_user(user)
    verification_code = pyotp.TOTP(user["otp_secret"],interval=600).now()
    verify_response = client.post("/auth/verify",json={"id":register_response.json()["id"],"verification_code":verification_code})
    # then create a new product by the new user
    product_response = client.post("/product",json=test_product,headers={"Authorization":f"Bearer {verify_response.json()['access_token']}"})
    response = client.get("/product/"+product_response.json()["id"])
    assert response.status_code == 200
    assert response.json()["name"] == test_product["name"]

def test_read_non_existing_item(clear_db):
    response = client.get("/product/78")
    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}

# test for correclty creating a new product
def test_create_product(clear_db):
    # first create a new user and verify it
    register_response = client.post("/auth/signup",json=test_user)
    user = User.find_one({"email":test_user["email"]})
    user = deserialize_user(user)
    verification_code = pyotp.TOTP(user["otp_secret"],interval=600).now()
    verify_response = client.post("/auth/verify",json={"id":register_response.json()["id"],"verification_code":verification_code})
    # then create a new product by the new user
    response = client.post("/product",json=test_product,headers={"Authorization":f"Bearer {verify_response.json()['access_token']}"})
    assert response.status_code == 201
    assert response.json()["name"] == test_product["name"]

def test_create_product_missing_field(clear_db):
    # first create a new user and verify it
    register_response = client.post("/auth/signup",json=test_user)  
    user = User.find_one({"email":test_user["email"]})
    user = deserialize_user(user)
    verification_code = pyotp.TOTP(user["otp_secret"],interval=600).now()
    verify_response = client.post("/auth/verify",json={"id":register_response.json()["id"],"verification_code":verification_code})
    # then create a new product by the new user
    response = client.post("/product",json={"name":"test","description":"test","price":100,"currency":"USD","category":"test","location":"test"},headers={"Authorization":f"Bearer {verify_response.json()['access_token']}"})
    assert response.status_code == 422
    assert response.json() == {
        'detail':[
            {
                'input': {
                    'name': 'test', 
                    'description': 'test', 
                    'price': 100, 
                    'currency': 'USD', 
                    'category': 'test', 
                    'location': 'test'}, 
                    'loc': [
                        'body', 
                        'condition'
                        ], 
                    'msg': 'Field required', 
                    'type': 'missing'
                }
            ]
        }
