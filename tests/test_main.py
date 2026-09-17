from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_item():
    """GET valide sur un item existant."""
    res = client.get("/items/1")
    assert res.status_code == 200
    assert res.json()["name"] == "Clavier"


def test_read_item_invalid_type():
    """GET avec un id non entier déclenchant une 422."""
    res = client.get("/items/abc")
    assert res.status_code == 422


def test_create_item():
    """POST valide créant un nouvel élément."""
    payload = {"name": "Écran", "price": 149.99}
    res = client.post("/items/", json=payload)
    assert res.status_code == 201
    assert res.json()["name"] == "Écran"