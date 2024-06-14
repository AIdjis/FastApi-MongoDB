from pydantic import BaseModel,EmailStr
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
    password: str


   

