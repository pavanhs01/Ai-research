import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def create(self, owner_id: uuid.UUID, data: ProjectCreate) -> Project:
        return await self.repo.create(owner_id, data)

    async def list_for_owner(self, owner_id: uuid.UUID) -> list[dict]:
        projects = await self.repo.list_for_owner(owner_id)
        results = []
        for p in projects:
            stats = await self.repo.get_stats(p.id)
            results.append({**p.__dict__, **stats})
        return results

    async def get_owned(self, project_id: uuid.UUID, owner_id: uuid.UUID) -> Project:
        project = await self.repo.get_by_id(project_id)
        if project is None:
            raise NotFoundException("Project not found.")
        if project.owner_id != owner_id:
            raise ForbiddenException("You do not have access to this project.")
        return project

    async def update(self, project: Project, data: ProjectUpdate) -> Project:
        return await self.repo.update(project, data)

    async def delete(self, project: Project) -> None:
        await self.repo.delete(project)
