from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class AuthorBase(BaseModel):
    surname: str
    family_name: str


class AuthorCreate(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BookBase(BaseModel):
    name: str
    description: Optional[str] = None
    stock: int
    stockTot: int
    genre: Optional[str] = None
    editor: Optional[str] = None
    id_author: int


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    stockTot: Optional[int] = None
    genre: Optional[str] = None
    editor: Optional[str] = None
    id_author: Optional[int] = None


class BookResponse(BookBase):
    id: int

    model_config = ConfigDict(from_attributes=True)