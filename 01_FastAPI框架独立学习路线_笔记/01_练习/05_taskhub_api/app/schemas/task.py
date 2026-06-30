from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import PageMeta
from app.schemas.project import ProjectSummary
from app.schemas.user import UserSummary


class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    done = "done"
    archived = "archived"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskTagInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=20)
    color: str = Field(default="#64748b", pattern=r"^#[0-9a-fA-F]{6}$")


class TaskTagRead(BaseModel):
    name: str
    color: str


class TaskBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    tags: list[TaskTagInput] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def validate_unique_tag_names(self):
        tag_names = [tag.name.lower() for tag in self.tags]
        if len(tag_names) != len(set(tag_names)):
            raise ValueError("tag names must be unique")
        return self


class TaskCreate(TaskBase):
    owner_id: int = Field(..., ge=1)
    project_id: int = Field(..., ge=1)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    owner_id: int | None = Field(default=None, ge=1)
    project_id: int | None = Field(default=None, ge=1)
    tags: list[TaskTagInput] | None = Field(default=None, max_length=5)

    @model_validator(mode="after")
    def validate_update_payload(self):
        if not self.model_fields_set:
            raise ValueError("At least one field is required")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")

        if "tags" in self.model_fields_set and self.tags is not None:
            tag_names = [tag.name.lower() for tag in self.tags]
            if len(tag_names) != len(set(tag_names)):
                raise ValueError("tag names must be unique")

        return self


class TaskListItem(BaseModel):
    id: int
    title: str
    status: TaskStatus
    priority: TaskPriority
    owner: UserSummary
    project: ProjectSummary
    tag_count: int
    updated_at: str


class TaskDetail(TaskListItem):
    description: str
    tags: list[TaskTagRead]
    created_at: str


class TaskListResponse(BaseModel):
    code: str
    message: str
    data: list[TaskListItem]
    meta: PageMeta


class TaskDetailResponse(BaseModel):
    code: str
    message: str
    data: TaskDetail
