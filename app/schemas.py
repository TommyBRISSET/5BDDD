from pydantic import BaseModel, Field


# --- Schémas Item ---
class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, examples=["Clavier"])
    price: float = Field(..., gt=0, examples=[49.99])
    is_offer: bool | None = Field(default=None, examples=[True])


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, examples=["Clavier RGB"])
    price: float | None = Field(default=None, gt=0, examples=[59.99])
    is_offer: bool | None = Field(default=None, examples=[True])


class ItemResponse(ItemBase):
    id: int

    class Config:
        from_attributes = True


# --- Schémas Authentification & User ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True