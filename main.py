import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import product
import os 
from app import database

app = FastAPI()

app.include_router(product.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.mount("/static", StaticFiles(directory="static"), name="static")



if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True,http="httptools")
