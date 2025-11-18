from fastapi import FastAPI
from config.db import db, client, close_client
from schema.user import User

app = FastAPI(title="FastAPI + MongoDB Test")

@app.get("/")
async def root(user: User):
    collections = await db["users"].find_one
    return {"message": "MongoDB connected!", "collections": collections}



