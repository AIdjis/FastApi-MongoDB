from fastapi.testclient import TestClient
from main import app
from .conftest import clear_db

client = TestClient(app)


# test for getting all products
def test_read_item(clear_db):
    response = client.get("/Products")
    assert response.status_code == 200
    assert len(response.json()) == 0


# test for correclty creating a new product
def test_create_product(clear_db):
    response = client.post("/Products",json={
        "name":"test",
        "description":"test",
        "price":100,
        "quantity":10,
        "is_available":True
    })
    assert response.status_code == 201
