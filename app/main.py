from fastapi import FastAPI, HTTPException, Response, status, Request
from app.schemas import ItemCreate, ItemResponse, ItemUpdate
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Demo FastAPI", version="0.1.0")

# Base de données simulée en mémoire
fake_db: dict[int, dict] = {
    1: {"name": "Clavier", "price": 49.99, "is_offer": True},
    2: {"name": "Souris", "price": 29.50, "is_offer": False},
}


# dossie fichiers HTML
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"titre": "Bienvenue sur mon application"},
    )


@app.get("/items/", response_model=list[ItemResponse])
def list_items(skip: int = 0, limit: int = 10):
    """Récupère une liste d'items paginée."""
    items = [{"id": k, **v} for k, v in fake_db.items()]
    return items[skip : skip + limit]


@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int):
    """Récupère un item spécifique par son ID."""
    if item_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )
    return {"id": item_id, **fake_db[item_id]}


@app.post(
    "/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED
)
def create_item(item: ItemCreate):
    """Crée un nouvel item validé par Pydantic."""
    new_id = max(fake_db.keys(), default=0) + 1
    fake_db[new_id] = item.model_dump()
    return {"id": new_id, **fake_db[new_id]}


@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item_update: ItemUpdate):
    """Met à jour les champs d'un item existant."""
    if item_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )

    # Récupère uniquement les champs renseignés dans la requête
    update_data = item_update.model_dump(exclude_unset=True)
    fake_db[item_id].update(update_data)

    return {"id": item_id, **fake_db[item_id]}


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    """Supprime un item par son ID."""
    if item_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item non trouvé"
        )
    del fake_db[item_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)