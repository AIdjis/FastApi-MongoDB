from pydantic import BaseModel,EmailStr,StringConstraints,Field
from typing import List,Union
from datetime import datetime



# product shemas
class ReadProduct(BaseModel):
    id:str
    name: str
    description: str
    price: float
    currency: str =Field(max_length=3)
    category: str
    location: str
    condition: str
    is_available: bool
    images_url: List[str]=[]
    create_at: Union[datetime, None]


class CreateProduct(BaseModel):
    name: str
    description: str
    price: float =Field(...,gt=0)
    category: str
    location: str
    condition: str
    currency: str =Field(default="USD",max_length=3)



# user authentication shemas
class CreateUser(BaseModel):
    name: str
    username: str=Field(...,max_length=30)
    email: EmailStr=Field(...,max_length=50)
    password: str =Field(...,min_length=8,max_length=64)

class LoginUser(BaseModel):
    email: EmailStr
    password: str =Field(...,min_length=8,max_length=64)

class ResponseUser(BaseModel):
    id:str
    email:EmailStr=Field(...,max_length=50)

class Verification(BaseModel):
    id: str
    verification_code:str

class ResendCode(BaseModel):
    email:EmailStr=Field(...,max_length=50)

class ForgotPassword(BaseModel):
    email:EmailStr=Field(...,max_length=50)
    password:str =Field(...,min_length=8,max_length=64)

# user profile schemas

class UserProfile(BaseModel):
    name:str
    username:str
    email:EmailStr=Field(...,max_length=50)
    created_at:Union[datetime,None]

class UpdateUserProfile(BaseModel):
    name:str
    username:str




   

