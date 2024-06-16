import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app import product
from app import authentication
import os 
import dotenv



dotenv.load_dotenv()
app = FastAPI()

app.include_router(product.product_router)
app.include_router(authentication.auth_router)

# enable the  cors 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
try:
    os.mkdir("static")
except FileExistsError:
    pass

app.mount("/static", StaticFiles(directory="static"), name="static")



if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True,http="httptools")
