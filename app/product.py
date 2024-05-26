from fastapi import APIRouter,status,HTTPException
from app.database import collection
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.schemas import ReadProduct,CreateProduct
from bson import ObjectId
from typing import List


# this is router for the products
router = APIRouter(prefix="/Products", tags=["Products"])


def deserialize_product(product)-> dict:
    return {
        'id':str(product["_id"]),
        'name':product["name"],
        'description':product["description"],
        'price':product["price"],
        'quantity':product["quantity"],
        'is_available':product["is_available"],
        }


#  this is a route for getting all products
@router.get("/",status_code=status.HTTP_200_OK,response_model=List[ReadProduct])
async def get_products():

    products = [deserialize_product(product) for product in collection.find()]   

    return products

# this is for getting a single product
@router.get("/{id}",status_code=status.HTTP_200_OK,response_model=ReadProduct)
async def get_product(id:str):
    product=collection.find_one({"_id":ObjectId(id)})
    if product==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    return deserialize_product(product)


# this is for creating a new product
@router.post("/",status_code=status.HTTP_201_CREATED,response_model=CreateProduct)
async def create_product(product:CreateProduct):
    collection.insert_one(dict(product))
    return product


# this is for deleting a product
@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(id:str):
    product=collection.find_one({"_id":ObjectId(id)})
    if product==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    collection.delete_one({"_id":ObjectId(id)})
    return {"details":"Product deleted"}






