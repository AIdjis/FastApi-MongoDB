from fastapi import APIRouter,Depends,HTTPException,status
from app.database import client
from bson import ObjectId
from datetime import datetime
from .security import jwt_required
from app.schemas import UserProfile

profile_router=APIRouter(prefix="/profile",tags=["Profile"])



def deserialize_data(user):
    return {"id":str(user["_id"]),
            "name":user["name"],
            "username":user["username"],
            "email":user["email"],
            "created_at":user["created_at"]}


@profile_router.get("/",status_code=status.HTTP_200_OK,response_model=UserProfile)
async def get_profile(user: dict =Depends(jwt_required)):
    profile=client.MarketPlace.users.find_one({"_id":ObjectId(user["id"])})
    if profile==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="profile not found")
    return deserialize_data(profile)


