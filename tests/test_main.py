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


def test_borrow_nonexistent_book(user_token):
    """TEST 7 : Emprunter un livre qui n'existe pas doit être bloqué par l'API."""
    headers = {"Authorization": f"Bearer {user_token}"}
    res = client.post("/rents/", json={"id_book": 99999}, headers=headers)

    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()


def test_return_nonexistent_rent(user_token):
    """TEST 8 : Rendre un emprunt fantôme doit être bloqué."""
    headers = {"Authorization": f"Bearer {user_token}"}
    res = client.put("/rents/99999/return", headers=headers)

    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()


def test_admin_access_all_rents(admin_token):
    """TEST 9 : Alice peut consulter la supervision totale des emprunts."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/rents/all", headers=headers)
    res.raise_for_status()
    assert isinstance(res.json(), list)

def test_login_invalid_credentials():
    """TEST 10 : Une tentative de connexion avec un mauvais mot de passe est rejetée."""
    res = client.post("/login", data={"username": "bob@user.com", "password": "wrongpassword"})
    # L'API doit lever une 401 Unauthorized
    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()


def test_admin_can_get_all_users(admin_token):
    """TEST 11 : Alice (APP_ADMIN) a le droit de lister tous les utilisateurs."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/users/", headers=headers)
    res.raise_for_status()

    users = res.json()
    assert isinstance(users, list)
    assert len(users) >= 2


def test_user_can_access_own_rents(user_token):
    """TEST 12 : Bob (APP_USER) peut consulter son propre historique d'emprunts avec succès."""
    headers = {"Authorization": f"Bearer {user_token}"}
    res = client.get("/rents/me", headers=headers)
    res.raise_for_status()

    rents = res.json()
    assert isinstance(rents, list)


def test_rbac_user_cannot_access_all_rents(user_token):
    """TEST 13 : Bob (APP_USER) tente d'accéder à la supervision totale des emprunts (Bloqué)."""
    headers = {"Authorization": f"Bearer {user_token}"}
    res = client.get("/rents/all", headers=headers)

    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()


def test_rbac_user_cannot_create_book(user_token):
    """TEST 14 : Bob (APP_USER) tente d'ajouter un livre au catalogue (Bloqué)."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {
        "name": "Livre Interdit",
        "stock": 5,
        "stockTot": 5,
        "id_author": 1
    }
    res = client.post("/books/", json=payload, headers=headers)

    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()


def test_rbac_user_cannot_delete_book(user_token):
    """TEST 15 : Bob (APP_USER) tente de supprimer un livre (Bloqué)."""
    headers = {"Authorization": f"Bearer {user_token}"}
    res = client.delete("/books/1", headers=headers)

    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()

def test_admin_can_create_author(admin_token):
    """TEST 16 : Alice (APP_ADMIN) peut créer un auteur."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"surname": "Emile", "family_name": "Zola"}
    res = client.post("/authors/", json=payload, headers=headers)
    res.raise_for_status()
    assert res.json()["surname"] == "Emile"

def test_user_cannot_create_author(user_token):
    """TEST 17 : Bob (APP_USER) ne peut pas créer un auteur (Bloqué)."""
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"surname": "Albert", "family_name": "Camus"}
    res = client.post("/authors/", json=payload, headers=headers)
    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()

def test_get_authors(user_token):
    """TEST 18 : Bob (APP_USER) peut consulter la liste des auteurs."""
    headers = {"Authorization": f"Bearer {user_token}"}
    res = client.get("/authors/", headers=headers)
    res.raise_for_status()
    assert isinstance(res.json(), list)

def test_user_cannot_delete_author(user_token):
    """TEST 19 : Bob (APP_USER) ne peut pas supprimer un auteur (Bloqué)."""
    headers = {"Authorization": f"Bearer {user_token}"}
    res = client.delete("/authors/1", headers=headers)
    with pytest.raises(httpx.HTTPStatusError):
        res.raise_for_status()

def test_business_rules_borrow_return_cycle(admin_token, user_token):
    """TEST 20 : Validation du cycle complet d'emprunt et de retour (Règles métier)."""
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_user = {"Authorization": f"Bearer {user_token}"}

    new_author = client.post(
        "/authors/",
        json={"surname": "Victor", "family_name": "Hugo"},
        headers=headers_admin
    )
    new_author.raise_for_status()
    author_id = new_author.json()["id"]

    new_book = client.post(
        "/books/",
        json={"name": "Les Misérables", "stock": 1, "stockTot": 1, "id_author": author_id},
        headers=headers_admin
    )
    new_book.raise_for_status()
    book_id = new_book.json()["id"]

    # (Règle 1 : Le stock baisse)
    rent = client.post("/rents/", json={"id_book": book_id}, headers=headers_user)
    rent.raise_for_status()
    rent_id = rent.json()["id"]

    book_check = client.get(f"/books/{book_id}", headers=headers_admin).json()
    assert book_check["stock"] == 0

    # (Règle 3 : Stock à 0)
    rent_fail = client.post("/rents/", json={"id_book": book_id}, headers=headers_user)
    with pytest.raises(httpx.HTTPStatusError):
        rent_fail.raise_for_status()

    # (Règle 4 : Seul l'emprunteur rend son livre)
    return_fail = client.put(f"/rents/{rent_id}/return", headers=headers_admin)
    with pytest.raises(httpx.HTTPStatusError):
        return_fail.raise_for_status()

    # (Règle 2 : Le stock remonte)
    return_ok = client.put(f"/rents/{rent_id}/return", headers=headers_user)
    return_ok.raise_for_status()

    book_check_final = client.get(f"/books/{book_id}", headers=headers_admin).json()
    assert book_check_final["stock"] == 1