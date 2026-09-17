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
from app.database import Base, engine, get_db
from app.models import Item, User
from app.schemas import (
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    TokenResponse,
)

settings = get_settings()
# Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="0.1.0")

# Init outil de hache
password_hash = PasswordHash.recommended()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
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

    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide : identifiant manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable en base de données",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

# ========================================== ROUTES ======================================================
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

@app.get(
    "/login-page",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    tags=["Pages"],
)
def login_page(request: Request):
    """Formulaire de connexion HTML."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
    )

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
    """Authentifie un user"""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(username=user.username)
    return {"access_token": token, "token_type": "bearer"}


@app.get(
    "/private",
    status_code=status.HTTP_200_OK,
    tags=["Authentification"],
)
def private_route(current_user: User = Depends(get_current_user)):
    """Route nécessite un Bearer token ok"""
    return {"message": f"Bonjour {current_user.username}"}

@app.get(
    "/dashboard",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    tags=["Pages"],
)
def dashboard_page(request: Request):
    """Affiche la page du tableau de bord."""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
    )

@app.get(
    "/items/",
    response_model=list[ItemResponse],
    status_code=status.HTTP_200_OK,
    tags=["Items"],
)
def list_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Item).offset(skip).limit(limit).all()


@app.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
    tags=["Items"],
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
)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
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
)
def update_item(item_id: int, item_update: ItemUpdate, db: Session = Depends(get_db)):
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
)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )
    db.delete(db_item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)