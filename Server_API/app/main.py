# main.py
# Description: This file contains the main FastAPI application, which serves as the primary API for the tldw application.
#
# Imports
#
# 3rd-party Libraries
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
#
# Local Imports
from .api.v1.endpoints.media import router as media_router
from .api.v1.endpoints.trash import router as trash_router
#
########################################################################################################################
#
# Functions:

app = FastAPI(
    title="tldw API",
    version="0.1.0",
    description="FastAPI Backend for the tldw project"
)

# -- If you have any global middleware, add it here --
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the tldw API"}

# Router for media endpoints/media file handling
app.include_router(media_router, prefix="/api/v1/media", tags=["media"])

# Router for trash endpoints - deletion of media items / trash file handling (FIXME: Secure delete vs lag on delete?)
app.include_router(trash_router, prefix="/api/v1/trash", tags=["trash"])

# Router for authentication endpoint
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
# The docs at http://localhost:8000/docs will show an “Authorize” button. You can log in by calling POST /api/v1/auth/login with a form that includes username and password. The docs interface is automatically aware because we used OAuth2PasswordBearer.


