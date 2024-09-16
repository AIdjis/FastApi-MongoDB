from fastapi import APIRouter,status,HTTPException,Response,UploadFile,File,Form,Request,Depends
from fastapi.responses import JSONResponse
from app.schemas import ReadProduct,CreateProduct,DeleteProductImages
from bson import ObjectId,errors
from typing import List
import secrets
import aiofiles
from datetime import datetime
import os
import re
from app.database import client
from app.security import jwt_required

# create the product collection
Product=client.MarketPlace.products


# this is router for the products
product_router = APIRouter(prefix="/product", tags=["Products"])


def deserialize_product(product)-> dict:
    return {
        'id':str(product["_id"]),
        'name':product["name"],
        'description':product["description"],
        'price':product["price"],
        'is_available':product["is_available"],
        'images_urls':product["images_urls"],
        'create_at':product["created_at"],
        'category':product["category"],
        'location':product["location"],
        'condition':product["condition"],
        'currency':product["currency"],
        'views':product["views"]
        }

def remove_images(images_urls:List[str]):
    for image in images_urls:
        path=re.findall(r'static/.+',image.url)
        os.remove(str(path[0]))

def is_valid_objectid(object_id : str)->bool:
    try:
        # Check if object_id can be converted to an ObjectId
        ObjectId(object_id)
        return True
    except errors.InvalidId:
        return False


#  this is a route for getting all products
@product_router.get("/",status_code=status.HTTP_200_OK,response_model=List[ReadProduct])
async def get_products():

    products = [deserialize_product(product) for product in Product.find()]   

    return products

# this is for getting a single product
@product_router.get("/{id}",status_code=status.HTTP_200_OK,response_model=ReadProduct)
async def get_product(id:str):
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    product=Product.find_one({"_id":ObjectId(id)})
    if product==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    product["views"]=product["views"]+1
    return deserialize_product(product)


# this is for creating a new product
@product_router.post("/",status_code=status.HTTP_201_CREATED,response_model=ReadProduct)
async def create_product(body:CreateProduct,Authorize:dict=Depends(jwt_required)):
    product=dict(body)
    product["created_at"]=datetime.today()
    product["is_available"]=True
    product["images_urls"]=[]
    product["user"]=Authorize["id"]
    product["views"]=0
    new_product=Product.insert_one(product)
    new_product=Product.find_one({"_id":new_product.inserted_id})
    return deserialize_product(new_product)


# this is for uploading images to the product
@product_router.patch("/upload/{id}",status_code=status.HTTP_201_CREATED)
async def upload_images(request:Request,id:str,images: List[UploadFile] = File(...),Authorize:dict=Depends(jwt_required)):
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    product = Product.find_one({"_id":ObjectId(id)})
    if product==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    if product["user"]!=Authorize["id"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized access")
    images_urls=[]
    for image in images:
        if image.content_type not in ['image/png','image/jpeg','image/jpg']:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='the file must be image')
    for image in images:
            destination_file_path = "static/"+secrets.token_hex(13)+image.filename 
            async with aiofiles.open(destination_file_path, 'wb') as out_file:
                 while content := await image.read(1024):  
                    await out_file.write(content) 
            images_urls.append(request.base_url._url+destination_file_path)

    product.update_one({"$set":{"images_urls":images_urls}})
    return JSONResponse(content={"detail":"images uploaded"})

# deleting a product from the database
@product_router.delete("/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(id:str,Authorize:dict=Depends(jwt_required)):
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    product=Product.find_one({"_id":ObjectId(id)})
    if product==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    if product["user"]!=Authorize["id"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized access")
    # removing images from the server (static folder)
    image_urls=product["images_urls"]
    await remove_images(image_urls)

    Product.delete_one({"_id":ObjectId(id)})
    return JSONResponse(content={"detail":"product deleted"})

# updating a single product 
@product_router.patch("/{id}",status_code=status.HTTP_202_ACCEPTED)
async def update_product(id:str,body:CreateProduct,Authorize:dict=Depends(jwt_required)):
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    product=Product.find_one({"_id":ObjectId(id)})
    if product==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    if product["user"]!=Authorize["id"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized access")
    product.update_one({"$set":dict(body)})
    return deserialize_product(product)

# removing images of the product
@product_router.delete("/delete-images/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_images(body:DeleteProductImages,id:str,Authorize:dict=Depends(jwt_required)):
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    product=Product.find_one({"_id":ObjectId(id)})
    if product==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Product not found")
    if product["user"]!=Authorize["id"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorized access")
    image_urls=body["images_url"]
    product_data=deserialize_product(product)
    # removing the images from the server and from the database
    stored_images=product_data["images_url"]
    for image_url in image_urls:
        if image_url not in stored_images:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="image not found")
        stored_images.remove(image_url)
    await remove_images(image_urls)
    product.update_one({"$set":{"images_url":stored_images}})
    return JSONResponse(content={"detail":"images deleted"})


