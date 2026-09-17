from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import Item
from app.schemas import ItemCreate, ItemResponse, ItemUpdate

# Récup config
settings = get_settings()

# Crée table dans Oracle
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/", response_class=HTMLResponse)
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


@app.get("/items/", response_model=list[ItemResponse])
def list_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Récupère la liste des items paginée depuis Oracle."""
    return db.query(Item).offset(skip).limit(limit).all()


@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    """Récupère un item spécifique depuis Oracle."""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )
    return item


@app.post(
    "/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED
)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)):
    """Insère un nouvel item dans Oracle avec validation Pydantic."""
    db_item = Item(**item_in.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int, item_update: ItemUpdate, db: Session = Depends(get_db)
):
    """Met à jour un item existant dans Oracle."""
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


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """Supprime un item dans Oracle."""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )
    db.delete(db_item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)