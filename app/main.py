from datetime import datetime, timedelta, timezone
from pathlib import Path
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Item, User
from app.schemas import (
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    TokenResponse,
)

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

password_hash = PasswordHash.recommended()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_oracle_roles(username: str, db: Session) -> list[str]:
    """Récupère les rôles Oracle associés à l'utilisateur depuis vues système."""
    query = text("""
        SELECT granted_role 
        FROM dba_role_privs 
        WHERE grantee = UPPER(:username)
    """)
    try:
        result = db.execute(query, {"username": username}).fetchall()
        return [row[0] for row in result]
    except Exception:
        return []


def create_access_token(username: str, roles: list[str]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": username,
        "roles": roles,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_user_token_data(token: str = Depends(oauth2_scheme)) -> dict:
    """Décode token et vérifie validité et expiration."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Le token a expiré, veuillez vous reconnecter",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(role_name: str):
    """Vérifie utilisateur possède rôle Oracle dans son token."""
    def role_checker(token_data: dict = Depends(get_current_user_token_data)):
        user_roles = [r.upper() for r in token_data.get("roles", [])]
        if role_name.upper() not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action refusée : privilège Oracle '{role_name.upper()}' requis.",
            )
        return token_data
    return role_checker

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/", response_class=HTMLResponse, status_code=status.HTTP_200_OK, tags=["Pages"])
def read_root(request: Request, db: Session = Depends(get_db)):
    db_connected = False
    try:
        db.execute(text("SELECT 1 FROM DUAL"))
        db_connected = True
    except Exception:
        db_connected = False

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "titre": f"Bienvenue sur {settings.app_name}",
            "db_connected": db_connected,
        },
    )


@app.get("/login-page", response_class=HTMLResponse, status_code=status.HTTP_200_OK, tags=["Pages"])
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.get("/dashboard", response_class=HTMLResponse, status_code=status.HTTP_200_OK, tags=["Pages"])
def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    tags=["Authentification"],
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """1. Vérifie mdp dans app_users
       2. Récupère rôles Oracle dans dba_role_privs
       3. Délivre JWT"""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Récupération rôles Oracle user
    oracle_roles = get_oracle_roles(user.username, db)

    # Création token
    token = create_access_token(username=user.username, roles=oracle_roles)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/private", status_code=status.HTTP_200_OK, tags=["Authentification"])
def private_route(token_data: dict = Depends(get_current_user_token_data)):
    """Route accessible à utilisateur authentifié"""
    username = token_data.get("sub")
    roles = token_data.get("roles", [])
    return {
        "message": f"Bonjour {username}",
        "roles_oracle": roles,
    }

@app.get(
    "/items/",
    response_model=list[ItemResponse],
    status_code=status.HTTP_200_OK,
    tags=["Items"],
    dependencies=[Depends(get_current_user_token_data)],
)
def list_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Lecture des items"""
    return db.query(Item).offset(skip).limit(limit).all()


@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    tags=["Items"],
    dependencies=[Depends(get_current_user_token_data)],
)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )
    return item


@app.post(
    "/items/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Items"],
    dependencies=[Depends(require_role("app_admin"))],
)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    """Création d'un item"""
    db_item = Item(**item_in.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    tags=["Items"],
    dependencies=[Depends(require_role("app_admin"))],
)
def update_item(item_id: int, item_update: ItemUpdate, db: Session = Depends(get_db)):
    """Mise à jour d'un item"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )

    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Items"],
    dependencies=[Depends(require_role("app_admin"))],
)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Suppression d'un item"""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )
    db.delete(db_item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)