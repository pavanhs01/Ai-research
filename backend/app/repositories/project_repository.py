import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.document import Document
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, owner_id: uuid.UUID, data: ProjectCreate) -> Project:
        project = Project(name=data.name, description=data.description, owner_id=owner_id)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def list_for_owner(self, owner_id: uuid.UUID) -> list[Project]:
        result = await self.db.execute(
            select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_stats(self, project_id: uuid.UUID) -> dict:
        doc_count = await self.db.scalar(
            select(func.count()).select_from(Document).where(Document.project_id == project_id)
        )
        conv_count = await self.db.scalar(
            select(func.count()).select_from(Conversation).where(Conversation.project_id == project_id)
        )
        return {"document_count": doc_count or 0, "conversation_count": conv_count or 0}

    async def update(self, project: Project, data: ProjectUpdate) -> Project:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.db.delete(project)
        await self.db.commit()
