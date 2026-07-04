from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, billing, chat, documents, projects, search

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(admin.router, prefix="/admin")
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
