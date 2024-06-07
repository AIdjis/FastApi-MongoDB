from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# test for getting all products
def test_read_item():
    response = client.get("/Products")
    assert response.status_code == 200


