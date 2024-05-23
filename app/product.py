from fastapi import APIRouter
from app.database import collection
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.schemas import Product
from bson import ObjectId

# this is router for the products
router = APIRouter(prefix="/Products", tags=["Products"])



async def deserialize_product(product)-> dict:
    return {
        'id':str(product["_id"]),
        'name':product["name"],
        'description':product["description"],
        'price':product["price"],
        'quantity':product["quantity"],
        'is_available':product["is_available"],}


#  this is a route for getting all products
@router.get("/")
async def get_products():

    products = [deserialize_product(product) for product in collection.find()]   

    return products




