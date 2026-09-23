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