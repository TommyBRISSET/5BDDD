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


@app.get("/books/", response_model=list[BookResponse], tags=["Books"], dependencies=[Depends(get_current_user_token_data)])
def get_books(db: Session = Depends(get_db), token_data: dict = Depends(get_current_user_token_data)):
    books = db.query(Book).all()
    if "APP_ADMIN" not in [r.upper() for r in token_data.get("roles", [])]:
        for book in books: book.stockTot = 0
    return books

@app.get("/books/{book_id}", response_model=BookResponse, tags=["Books"], dependencies=[Depends(get_current_user_token_data)])
def get_book(book_id: int, db: Session = Depends(get_db), token_data: dict = Depends(get_current_user_token_data)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book: raise HTTPException(status_code=404, detail="Livre non trouvé")
    if "APP_ADMIN" not in [r.upper() for r in token_data.get("roles", [])]: book.stockTot = 0
    return book

@app.post("/books/", response_model=BookResponse, status_code=201, tags=["Books"], dependencies=[Depends(require_role("app_admin"))])
def create_book(book_in: BookCreate, db: Session = Depends(get_db)):
    db_book = Book(**book_in.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.put("/books/{book_id}", response_model=BookResponse, tags=["Books"], dependencies=[Depends(require_role("app_admin"))])
def update_book(book_id: int, book_in: BookUpdate, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book: raise HTTPException(status_code=404, detail="Livre non trouvé")
    for key, value in book_in.model_dump(exclude_unset=True).items(): setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}", status_code=204, tags=["Books"], dependencies=[Depends(require_role("app_admin"))])
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book: raise HTTPException(status_code=404, detail="Livre non trouvé")
    db.delete(db_book)
    db.commit()
    return Response(status_code=204)


@app.post("/rents/", response_model=RentBookResponse, status_code=201, tags=["Emprunts"])
def borrow_book(rent_in: RentBookCreate, db: Session = Depends(get_db),
                token_data: dict = Depends(get_current_user_token_data)):
    user = db.query(User).filter(User.email == token_data.get("sub")).first()
    book = db.query(Book).filter(Book.id == rent_in.id_book).first()

    if not book: raise HTTPException(status_code=404, detail="Livre non trouvé")
    if book.stock <= 0: raise HTTPException(status_code=400, detail="Ce livre n'est plus disponible.")

    book.stock -= 1
    db_rent = RentBook(id_book=book.id, id_user=user.id)
    db.add(db_rent)
    db.commit()
    db.refresh(db_rent)
    return db_rent


@app.put("/rents/{rent_id}/return", response_model=RentBookResponse, tags=["Emprunts"])
def return_book(rent_id: int, db: Session = Depends(get_db), token_data: dict = Depends(get_current_user_token_data)):
    user = db.query(User).filter(User.email == token_data.get("sub")).first()
    rent = db.query(RentBook).filter(RentBook.id == rent_id).first()

    if not rent: raise HTTPException(status_code=404, detail="Emprunt introuvable")
    if rent.id_user != user.id: raise HTTPException(status_code=403,
                                                    detail="Vous ne pouvez pas rendre un livre que vous n'avez pas emprunté.")
    if rent.dateEnd is not None: raise HTTPException(status_code=400, detail="Ce livre a déjà été rendu.")

    rent.dateEnd = datetime.now()
    rent.book.stock += 1
    db.commit()
    db.refresh(rent)
    return rent


@app.get("/rents/me", response_model=list[RentBookResponse], tags=["Emprunts"])
def get_my_rents(db: Session = Depends(get_db), token_data: dict = Depends(get_current_user_token_data)):
    user = db.query(User).filter(User.email == token_data.get("sub")).first()
    return db.query(RentBook).filter(RentBook.id_user == user.id).all()


@app.get("/rents/all", response_model=list[RentBookResponse], tags=["Emprunts"],
         dependencies=[Depends(require_role("app_admin"))])
def get_all_rents(db: Session = Depends(get_db)):
    return db.query(RentBook).all()


@app.get("/users/", response_model=list[UserResponse], tags=["Utilisateurs"],
         dependencies=[Depends(require_role("app_admin"))])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@app.post("/users/", response_model=UserResponse, status_code=201, tags=["Utilisateurs"],
          dependencies=[Depends(require_role("app_admin"))])
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user_data = user_in.model_dump()
    user_data["password"] = get_password_hash(user_in.password)
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.put("/users/{user_id}", response_model=UserResponse, tags=["Utilisateurs"],
         dependencies=[Depends(require_role("app_admin"))])
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user: raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])

    for key, value in update_data.items(): setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user