from fastapi import APIRouter,status,HTTPException,Response,UploadFile,File,Form,Request
from app.database import collection
from fastapi.responses import JSONResponse
from app.schemas import ReadProduct,CreateProduct
from bson import ObjectId
from typing import List
import secrets
import aiofiles
from datetime import datetime
import os


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
        'images_url':product["images_url"],
        'create_at':product["create_at"]
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
@router.post("/",status_code=status.HTTP_201_CREATED,response_model=ReadProduct)
async def create_product(product:CreateProduct):
    product=dict(product)
    product["create_at"]=datetime.now()
    product["images_url"]=[]
    new_product=collection.insert_one(product)
    new_product=collection.find_one({"_id":new_product.inserted_id})
    return deserialize_product(new_product)

@router.post("/upload/{id}",status_code=status.HTTP_201_CREATED)
async def upload_image(request:Request,id:str,images: List[UploadFile] = File(...)):
    images_url=[]
    for image in images:
        if image.content_type not in ['image/png','image/jpeg','image/jpg']:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='the file must be image')
    for image in images:
            destination_file_path = "static/"+secrets.token_hex(13)+image.filename 
            async with aiofiles.open(destination_file_path, 'wb') as out_file:
                 while content := await image.read(1024):  
                    await out_file.write(content) 
            images_url.append(destination_file_path)

    collection.update_one({"_id":ObjectId(id)},{"$set":{"images_url":images_url}})
    return {"details":"image uploaded"}

# this is for deleting a product
@router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(id:str):
    product=collection.find_one({"_id":ObjectId(id)})
    # removing images from the server (static folder)
    for image in product["images_url"]:
        os.remove(str(image))
    if product==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    collection.delete_one({"_id":ObjectId(id)})
    return {"details":"Product deleted"}


# this is for updating a product
@router.patch("/{id}",status_code=status.HTTP_202_ACCEPTED)
async def update_product(id:str,product:CreateProduct):
    # print(dict(product))
    product_mapped=collection.find_one_and_update({"_id":ObjectId(id)},{"$set":dict(product)})    
    if product_mapped==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    
    product_updated=collection.find_one({"_id":ObjectId(id)})
    return deserialize_product(product_updated)






