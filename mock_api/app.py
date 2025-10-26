from fastapi import FastAPI
from .api.applications import router as applications_router

app = FastAPI()

app.include_router(applications_router)