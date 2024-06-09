from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# test for getting all products
def test_read_item():
    response = client.get("/Products")
    assert response.status_code == 200

# test for creating a new product
def test_create_product():
    response = client.post("/Products",json={
        "name":"test",
        "description":"test",
        "price":100,
        "quantity":10,
        "is_available":True
    })
    assert response.status_code == 201
