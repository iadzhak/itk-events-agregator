from pydantic import BaseModel, Field, HttpUrl, PositiveInt

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MIN_PAGE_SIZE = 1
MAX_PAGE_SIZE = 100


class Pagination(BaseModel):
    page: PositiveInt = Field(DEFAULT_PAGE, description='Номер страницы')
    page_size: PositiveInt = Field(
        DEFAULT_PAGE_SIZE,
        ge=MIN_PAGE_SIZE,
        le=MAX_PAGE_SIZE,
        description='Количество записей',
    )


class PaginatedResponse[T](BaseModel):
    count: int
    next: HttpUrl | None
    previous: HttpUrl | None
    results: list[T]
