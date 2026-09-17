from sqlalchemy import Boolean, Column, Float, Integer, String
from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    is_offer = Column(Boolean, default=False, nullable=True)