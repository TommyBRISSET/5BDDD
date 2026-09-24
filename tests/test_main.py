import pytest
import httpx
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings

client = TestClient(app)
settings = get_settings()


@pytest.fixture
def admin_token():
    """Génère un token valide pour Alice (APP_ADMIN)."""
    res = client.post("/login", data={"username": "alice@admin.com", "password": "secret"})
    res.raise_for_status()
    return res.json()["access_token"]

@pytest.fixture
def user_token():
    """Génère un token valide pour Bob (APP_USER)."""
    res = client.post("/login", data={"username": "bob@user.com", "password": "secret"})
    res.raise_for_status()
    return res.json()["access_token"]


def test_valid_token(admin_token):
    """TEST 1 : Un token valide donne bien accès à la route privée."""
    res = client.get("/private", headers={"Authorization": f"Bearer {admin_token}"})
    res.raise_for_status()
    assert res.json()["email"] == "alice@admin.com"


def test_malformed_token():
    """TEST 2 : Un token mal formaté est rejeté par l'API."""
    res = client.get("/private", headers={"Authorization": "Bearer token.completement.faux"})
    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()


def test_expired_token():
    """TEST 3 : Un token dont la date est dépassée est rejeté."""
    payload = {
        "sub": "alice@admin.com",
        "roles": ["APP_ADMIN"],
        "exp": datetime.now(timezone.utc) - timedelta(minutes=10)
    }
    expired_token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    res = client.get("/private", headers={"Authorization": f"Bearer {expired_token}"})
    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()

def test_rbac_user_cannot_create_users(user_token):
    """TEST 4 : Bob (APP_USER) ne peut pas créer de nouveaux utilisateurs."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"surname": "Hack", "family_name": "Er", "email": "hack@hacker.com", "password": "123"}

    res = client.post("/users/", json=payload, headers=headers)

    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()


def test_total_stock_hidden_for_user(user_token):
    """TEST 5 : Règle métier - Bob ne doit pas voir le stock total des livres."""
    headers = {"Authorization": f"Bearer {user_token}"}
    res = client.get("/books/", headers=headers)
    res.raise_for_status()

    books = res.json()
    for book in books:
        assert book["stockTot"] == 0


def test_total_stock_visible_for_admin(admin_token):
    """TEST 6 : Règle métier - Alice doit pouvoir voir le vrai stock total (si des livres existent)."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/books/", headers=headers)
    res.raise_for_status()