from pydantic import BaseModel


class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
    tags: list[str] = []
    in_stock: bool = True
