from sqlalchemy import Boolean, Column, Float, Integer, Sequence, String
from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(
        Integer,
        Sequence("items_id_seq", start=1, increment=1),
        primary_key=True,
        index=True,
    )
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    is_offer = Column(Boolean, default=False, nullable=True)