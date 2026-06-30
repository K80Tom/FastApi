from pydantic import BaseModel


class ProjectSummary(BaseModel):
    id: int
    name: str
