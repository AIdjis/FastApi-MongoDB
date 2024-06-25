import pytest
from pymongo.mongo_client import MongoClient
import dotenv
import os

dotenv.load_dotenv(".env")

@pytest.fixture(scope="function")
def database():
    client = MongoClient(os.getenv("DB_URL"))
    db = client.MarketPlace

   
    yield db
    
    # close the connection
    client.close()
    

@pytest.fixture(scope="function")
def clear_db(database):
    db=database
    # Cleanup before running a test
    for collection in db.list_collection_names():
        db[collection].delete_many({})
    yield db
    