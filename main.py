from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from database.session import get_session, create_db_and_tables
from models.book import Book, BookCreate, BookUpdate

app = FastAPI(
    title="Book Inventory API",
    version="1.0.0"
)
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/books", response_model=Book, status_code=201)
def create_book(book: BookCreate, session: Session = Depends(get_session)):
    db_book = Book(**book.dict())
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


@app.get("/books", response_model=List[Book])
def list_books(
    author: Optional[str] = None,
    available: Optional[bool] = None,
    session: Session = Depends(get_session)
):
    query = select(Book)

    if author:
        query = query.where(Book.author == author)

    if available is not None:
        query = query.where(Book.available == available)

    return session.exec(query).all()
@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.patch("/books/{book_id}", response_model=Book)
def update_book(
    book_id: int,
    book_update: BookUpdate,
    session: Session = Depends(get_session)
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    for key, value in book_update.dict(exclude_unset=True).items():
        setattr(book, key, value)

    book.updated_at = datetime.utcnow()
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    session.delete(book)
    session.commit()
    return None


@app.get("/books/search", response_model=List[Book])
def search_books(q: str, session: Session = Depends(get_session)):
    query = select(Book).where(
        (Book.title.contains(q)) |
        (Book.author.contains(q))
    )
    return session.exec(query).all()