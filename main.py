# main.py
from fastapi import FastAPI
from config.db import db, client, close_client  # client is optional

app = FastAPI(title="FastAPI + MongoDB Test")

@app.get("/")
async def root():
    # simple test: list collection names
    collections = await db.list_collection_names()
    return {"message": "MongoDB connected!", "collections": collections}

@app.on_event("shutdown")
def shutdown_event():
    # close mongodb client on shutdown
    close_client()
