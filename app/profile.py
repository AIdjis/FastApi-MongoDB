from fastapi import APIRouter,Depends,HTTPException,status,Response,UploadFile,File,Request
from fastapi.responses import JSONResponse
from app.database import client
from bson import ObjectId
from datetime import datetime
from .security import jwt_required,verify_password
from app.schemas import UserProfile,UpdateUserProfile,ReadUserProfile,DeleteUserProfile
import secrets
import aiofiles
from app.authentication import username_regex

profile_router=APIRouter(prefix="/profile",tags=["Profile"])

User=client.MarketPlace.users


def deserialize_data(user):
    return {"id":str(user["_id"]),
            "name":user["name"],
            "username":user["username"],
            "email":user["email"],
            "created_at":user["created_at"],
            "picture":user["picture"],
            "password":user["password"],}

# retrieve user profile data publicly accessible for everyone
@profile_router.get("/{user_name}",status_code=status.HTTP_200_OK,response_model=UserProfile)
async def get_profile(user_name:str):
    profile=User.find_one({"username": user_name})
    if profile==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    return deserialize_data(profile)

# retrieve user profile data only for authenticated users
@profile_router.get("/",status_code=status.HTTP_200_OK,response_model=ReadUserProfile)
async def get_profile_me(Authorize: dict = Depends(jwt_required)):
    profile=User.find_one({"_id":ObjectId(Authorize["id"])})
    if profile==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    return deserialize_data(profile)

#logout the user
@profile_router.get('/logout', status_code=status.HTTP_200_OK)
async def logout(response: Response, Authorize: dict = Depends(jwt_required)):
    response.delete_cookie(key='access_token', domain=None, httponly=True, samesite="lax")
    response.delete_cookie(key='refresh_token', domain=None, httponly=True, samesite="lax")
    response.set_cookie('logged_in', '', -1)
    return {'detail': 'success'}

#upload profile picture of the user
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

# update user profile
@profile_router.patch('/update', status_code=status.HTTP_200_OK)
async def update_profile(body: UpdateUserProfile, Authorize: dict = Depends(jwt_required)):
    user= User.find_one({"_id":ObjectId(Authorize["id"])})
    if user==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    if User.find_one({"username":body.username}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username already taken")
    if not username_regex.match(body.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="invalid username")
    User.update_one({"_id":ObjectId(Authorize["id"])},{"$set":dict(body)})
    return deserialize_data(user)

# delete user profile only for authenticated users 
# required a password to delete the User 
@profile_router.delete('/delete', status_code=status.HTTP_200_OK)
async def delete_profile(body: DeleteUserProfile,Authorize: dict = Depends(jwt_required)):
    user= User.find_one({"_id":ObjectId(Authorize["id"])})
    if user==None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    # checking if the password is correct
    user_data=deserialize_data(user)
    if not verify_password(body["password"],user_data["password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="password is incorrect")
    User.delete_one({"_id":ObjectId(Authorize["id"])})
    return deserialize_data(user)
