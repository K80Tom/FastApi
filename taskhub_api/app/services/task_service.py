from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError
from app.db.transaction import transaction
from app.models.tag import Tag
from app.models.task import Task
from app.models.user import User
from app.repositories import task_repository
from app.schemas.task import TagInput, TaskCreate, TaskUpdate
from app.services.permission_service import require_project_role


async def get_existing_task(session: AsyncSession, task_id: int) -> Task:
    task = await task_repository.get(session, task_id)
    if task is None:
        raise NotFoundError("Task not found", details={"task_id": task_id})
    return task


async def resolve_tags(session: AsyncSession, project_id: int, inputs: list[TagInput]) -> list[Tag]:
    normalized = [item.name.lower() for item in inputs]
    if len(normalized) != len(set(normalized)):
        from app.core.errors import ConflictError

        raise ConflictError("Tag names must be unique within a task")
    tags: list[Tag] = []
    for item in inputs:
        result = await session.execute(select(Tag).where(Tag.project_id == project_id, Tag.name == item.name))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = Tag(project_id=project_id, name=item.name, color=item.color)
            session.add(tag)
            await session.flush()
        tags.append(tag)
    return tags


async def list_tasks(session: AsyncSession, user: User, **query) -> tuple[list[Task], int]:
    # 管理员可见全部任务；普通用户只能看到自己加入的项目。
    visible_user_id = None if user.role == "admin" else user.id
    return await task_repository.list_visible(session, visible_user_id, **query)


async def get_task(session: AsyncSession, user: User, task_id: int) -> Task:
    task = await get_existing_task(session, task_id)
    await require_project_role(session, user, task.project_id, "viewer")
    return task


async def create_task(session: AsyncSession, user: User, payload: TaskCreate) -> Task:
    async with transaction(session):
        await require_project_role(session, user, payload.project_id, "member")
        tags = await resolve_tags(session, payload.project_id, payload.tags)
        task = await task_repository.create(
            session,
            project_id=payload.project_id,
            owner_id=user.id,
            title=payload.title,
            description=payload.description,
            status=payload.status.value,
            priority=payload.priority.value,
            tags=tags,
        )
        task_id = task.id
    return await get_existing_task(session, task_id)


async def update_task(session: AsyncSession, user: User, task_id: int, payload: TaskUpdate) -> Task:
    async with transaction(session):
        task = await get_existing_task(session, task_id)
        _, project_role = await require_project_role(session, user, task.project_id, "member")
        if user.role != "admin" and project_role != "owner" and task.owner_id != user.id:
            raise ForbiddenError("Only the task owner or project owner can update this task")
        changes = payload.model_dump(exclude_unset=True, exclude={"tags"})
        if "status" in changes:
            changes["status"] = changes["status"].value
        if "priority" in changes:
            changes["priority"] = changes["priority"].value
        for name, value in changes.items():
            setattr(task, name, value)
        if "tags" in payload.model_fields_set:
            task.tags = await resolve_tags(session, task.project_id, payload.tags or [])
        await session.flush()
    return await get_existing_task(session, task_id)


async def delete_task(session: AsyncSession, user: User, task_id: int) -> None:
    async with transaction(session):
        task = await get_existing_task(session, task_id)
        _, project_role = await require_project_role(session, user, task.project_id, "member")
        if user.role != "admin" and project_role != "owner" and task.owner_id != user.id:
            raise ForbiddenError("Only the task owner or project owner can delete this task")
        await task_repository.delete(session, task)


async def add_comment(session: AsyncSession, user: User, task_id: int, content: str):
    async with transaction(session):
        task = await get_existing_task(session, task_id)
        await require_project_role(session, user, task.project_id, "member")
        return await task_repository.create_comment(session, task_id, user.id, content)


async def list_comments(session: AsyncSession, user: User, task_id: int):
    task = await get_existing_task(session, task_id)
    await require_project_role(session, user, task.project_id, "viewer")
    return await task_repository.list_comments(session, task_id)
