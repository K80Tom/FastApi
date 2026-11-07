from pydantic import BaseModel


class DataResponse[DataT](BaseModel):
    code: str = "OK"
    message: str = "success"
    data: DataT


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PageResponse[DataT](BaseModel):
    code: str = "OK"
    message: str = "success"
    data: list[DataT]
    meta: PageMeta


def page_meta(page: int, page_size: int, total: int) -> PageMeta:
    total_pages = (total + page_size - 1) // page_size if total else 0
    return PageMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1 and total_pages > 0,
    )
