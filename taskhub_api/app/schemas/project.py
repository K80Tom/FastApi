from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    owner_id: int


class MemberAdd(BaseModel):
    user_id: int = Field(ge=1)
    role: Literal["member", "viewer"] = "member"


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_id: int
    user_id: int
    role: str
