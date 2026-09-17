from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    """Schéma de base contenant les attributs partagés."""

    name: str = Field(..., min_length=1, examples=["Clavier"])
    price: float = Field(..., gt=0, examples=[49.99])
    is_offer: bool | None = Field(default=None, examples=[True])


class ItemCreate(ItemBase):
    """Schéma utilisé pour la création d'un item via POST."""

    pass


class ItemUpdate(BaseModel):
    """Schéma utilisé pour la mise à jour (PUT/PATCH)."""

    name: str | None = Field(default=None, min_length=1, examples=["Clavier RGB"])
    price: float | None = Field(default=None, gt=0, examples=[59.99])
    is_offer: bool | None = Field(default=None, examples=[True])


class ItemResponse(ItemBase):
    """Schéma utilisé pour la réponse de l'API avec son identifiant."""

    id: int

    class Config:
        from_attributes = True