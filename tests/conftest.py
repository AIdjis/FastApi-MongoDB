import pytest
from pymongo.mongo_client import MongoClient
import dotenv
import os

dotenv.load_dotenv(".env")
   

@pytest.fixture(scope="function")
def clear_db():
    client = MongoClient(os.getenv("DB_URL"))
    db = client.MarketPlace
    # Cleanup after running a test


    yield db

    for collection in db.list_collection_names():
        db[collection].delete_many({})

    client.close()
    
    