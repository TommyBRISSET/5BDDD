from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Sequence, String
from sqlalchemy.orm import relationship
from app.database import Base


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, Sequence("authors_id_seq", start=1, increment=1), primary_key=True)
    surname = Column(String(50), nullable=False)
    family_name = Column(String(50), nullable=False)

    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, Sequence("books_id_seq", start=1, increment=1), primary_key=True)
    name = Column(String(150), nullable=False)
    description = Column(String(500))
    stock = Column(Integer, nullable=False, default=0)
    stockTot = Column(Integer, nullable=False, default=0)
    genre = Column(String(50))
    editor = Column(String(100))

    id_author = Column(Integer, ForeignKey("authors.id"), nullable=False)

    author = relationship("Author", back_populates="books")
    rents = relationship("RentBook", back_populates="book")


class User(Base):
    __tablename__ = "app_users"

    id = Column(Integer, Sequence("app_users_id_seq", start=1, increment=1), primary_key=True)
    surname = Column(String(50), nullable=False)
    family_name = Column(String(50), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    blacklist = Column(Boolean, default=False, nullable=False)

    rents = relationship("RentBook", back_populates="user")


class RentBook(Base):
    __tablename__ = "rent_books"

    id = Column(Integer, Sequence("rent_books_id_seq", start=1, increment=1), primary_key=True)
    id_book = Column(Integer, ForeignKey("books.id"), nullable=False)
    id_user = Column(Integer, ForeignKey("app_users.id"), nullable=False)
    dateBeginRen = Column(DateTime, default=datetime.now, nullable=False)
    dateEnd = Column(DateTime, nullable=True)

    book = relationship("Book", back_populates="rents")
    user = relationship("User", back_populates="rents")