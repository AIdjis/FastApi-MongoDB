from fastapi import APIRouter,Depends,HTTPException,status,Response
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

# retrieve user profile data
@profile_router.get("/",status_code=status.HTTP_200_OK,response_model=UserProfile)
async def get_profile(user: dict =Depends(jwt_required)):
    profile=client.MarketPlace.users.find_one({"_id":ObjectId(user["id"])})
    if profile==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="profile not found")
    return deserialize_data(profile)

#logout the user
@profile_router.get('/logout', status_code=status.HTTP_200_OK)
def logout(response: Response, Authorize: dict = Depends(jwt_required)):
    response.delete_cookie(key='access_token', domain=None, httponly=True, samesite="lax")
    response.delete_cookie('refresh_token', domain=None, httponly=True, samesite="lax")
    response.set_cookie('logged_in', '', -1)
    return {'detail': 'success'}



