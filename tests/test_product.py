from fastapi.testclient import TestClient
from pymongo.mongo_client import MongoClient
from main import app
import pytest
import dotenv
import os

client = TestClient(app)



dotenv.load_dotenv(".env")

@pytest.fixture(scope="function")
def setup_db():
    client = MongoClient(os.getenv("DB_URL"))
    db = client.MarketPlace

    # Cleanup before running a test
    yield db
    
    # Cleanup after running a test
    for collection in db.list_collection_names():
        db[collection].delete_many({})

    client.close()




# test for getting all products

def test_read_item(setup_db):
    response = client.get("/Products")
    assert response.status_code == 200
    assert len(response.json()) == 0
    

def test_create_product(setup_db):
    response = client.post("/Products",json={
        "name":"test",
        "description":"test",
        "price":100,
        "quantity":10,
        "is_available":True
    })
    assert response.status_code == 201
