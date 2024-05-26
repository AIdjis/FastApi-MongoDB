from pydantic import BaseModel


# read the product
class ReadProduct(BaseModel):
    id:str
    name: str
    description: str
    price: float
    quantity: int
    is_available: bool




# create the product
class CreateProduct(BaseModel):
    name: str
    description: str
    price: float
    quantity: int
    is_available: bool
   

