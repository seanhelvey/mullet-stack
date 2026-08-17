from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_items_returns_all_items():
    response = client.get("/items")
    assert response.status_code == 200

    items = response.json()
    assert len(items) == 3
    assert items[0]["name"] == "Enamel mug"


def test_list_items_matches_the_item_shape():
    response = client.get("/items")
    item = response.json()[0]

    assert set(item.keys()) == {"id", "name", "description", "tags", "in_stock"}
    assert isinstance(item["tags"], list)
