import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_db_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, ProjectWithStats
from app.services.project_service import ProjectService

router = APIRouter()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    return await ProjectService(db).create(user.id, payload)


@router.get("", response_model=list[ProjectWithStats])
async def list_projects(user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)):
    return await ProjectService(db).list_for_owner(user.id)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    return await ProjectService(db).get_owned(project_id, user.id)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    project = await service.get_owned(project_id, user.id)
    return await service.update(project, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID, user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)
):
    service = ProjectService(db)
    project = await service.get_owned(project_id, user.id)
    await service.delete(project)
