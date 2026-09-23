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
from app.models import Author, Book, User, RentBook
from app.schemas import (
    TokenResponse,
    AuthorCreate, AuthorResponse,
    BookCreate, BookUpdate, BookResponse,
    UserCreate, UserUpdate, UserResponse,
    RentBookCreate, RentBookResponse
)

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
password_hash = PasswordHash.recommended()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def get_oracle_roles(surname: str, db: Session) -> list[str]:
    query = text("SELECT granted_role FROM dba_role_privs WHERE grantee = UPPER(:username)")
    try:
        return [row[0] for row in db.execute(query, {"username": surname}).fetchall()]
    except Exception:
        return []

def create_access_token(username: str, roles: list[str]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "roles": roles, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def get_current_user_token_data(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

def require_role(role_name: str):
    def role_checker(token_data: dict = Depends(get_current_user_token_data)):
        user_roles = [r.upper() for r in token_data.get("roles", [])]
        if role_name.upper() not in user_roles:
            raise HTTPException(status_code=403, detail=f"Privilège Oracle '{role_name.upper()}' requis.")
        return token_data
    return role_checker

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse, tags=["Pages"])
def read_root(request: Request, db: Session = Depends(get_db)):
    db_connected = False
    try:
        db.execute(text("SELECT 1 FROM DUAL"))
        db_connected = True
    except Exception:
        pass
    return templates.TemplateResponse(request=request, name="index.html", context={"titre": settings.app_name, "db_connected": db_connected})

@app.post("/login", response_model=TokenResponse, tags=["Authentification"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if user.blacklist:
        raise HTTPException(status_code=403, detail="Votre compte a été placé sur liste noire.")

    oracle_roles = get_oracle_roles(user.surname.lower(), db)
    token = create_access_token(username=user.email, roles=oracle_roles)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/private", tags=["Authentification"])
def read_users_me(token_data: dict = Depends(get_current_user_token_data)):
    return {"email": token_data.get("sub"), "roles_oracle": token_data.get("roles", [])}
