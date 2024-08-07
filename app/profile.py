from fastapi import APIRouter,Depends,HTTPException,status,Response,UploadFile,File,Request
from fastapi.responses import JSONResponse
from app.database import client
from bson import ObjectId
from datetime import datetime
from .security import jwt_required
from app.schemas import UserProfile
import secrets
import aiofiles

profile_router=APIRouter(prefix="/profile",tags=["Profile"])

User=client.MarketPlace.users


def deserialize_data(user):
    return {"id":str(user["_id"]),
            "name":user["name"],
            "username":user["username"],
            "email":user["email"],
            "created_at":user["created_at"]}

# retrieve user profile data
@profile_router.get("/",status_code=status.HTTP_200_OK,response_model=UserProfile)
async def get_profile(user: dict =Depends(jwt_required)):
    profile=User.find_one({"_id":ObjectId(user["id"])})
    if profile==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    return deserialize_data(profile)

#logout the user
@profile_router.get('/logout', status_code=status.HTTP_200_OK)
def logout(response: Response, Authorize: dict = Depends(jwt_required)):
    response.delete_cookie(key='access_token', domain=None, httponly=True, samesite="lax")
    response.delete_cookie('refresh_token', domain=None, httponly=True, samesite="lax")
    response.set_cookie('logged_in', '', -1)
    return {'detail': 'success'}


@profile_router.post('/upload', status_code=status.HTTP_200_OK)
async def upload_picture(request: Request, picture: UploadFile = File(...),Authorize: dict = Depends(jwt_required)):
    user= User.find_one({"_id":ObjectId(Authorize["id"])})
    if user==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    if picture.content_type not in ['image/png', 'image/jpeg', 'image/jpg']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='the file must be image')

    destination_file_path = "static/" + secrets.token_hex(13) + picture.filename
    async with aiofiles.open(destination_file_path, 'wb') as out_file:
        while content := await picture.read(1024):
            await out_file.write(content)
    User.update_one({"_id":ObjectId(Authorize["id"])},{"$set":{"picture":request.base_url._url+destination_file_path}})
    
    return JSONResponse(content={"detail": "image uploaded"})

