from pydantic import BaseModel,EmailStr,StringConstraints,Field
from typing import List,Union
from datetime import datetime



# read the product
class ReadProduct(BaseModel):
    id:str
    name: str
    description: str
    price: float
    quantity: int
    is_available: bool
    images_url: List[str]=[]
    create_at: Union[datetime, None]
    




# create the product
class CreateProduct(BaseModel):
    name: str
    description: str
    price: float
    quantity: int
    is_available: bool


# create the user
class CreateUser(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str =Field(...,min_length=8,max_length=64)

class LoginUser(BaseModel):
    email: EmailStr
    password: str =Field(...,min_length=8,max_length=64)

class ResponseUser(BaseModel):
    id:str
    email:EmailStr

class Verification(BaseModel):
    id: str
    verification_code:str
   

