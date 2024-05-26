from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import dotenv


#Load environment variables
dotenv.load_dotenv()
url=os.getenv("DB_URL")

#Create a new client and connect to the server
client = MongoClient(url, server_api=ServerApi('1'))
#Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    # print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


#Create database and collection
db = client.MarketPlace
collection = db["products"]
