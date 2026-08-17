from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import Item

app = FastAPI(title="mullet-stack backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
)

ITEMS = [
    Item(id=1, name="Enamel mug", tags=["kitchen", "camping"]),
    Item(id=2, name="Field notebook", description="Grid pages, pocket-sized", tags=["stationery"]),
    Item(id=3, name="Multitool", tags=["hardware"], in_stock=False),
]


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    return ITEMS
