import strawberry
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
from strawberry.fastapi import GraphQLRouter
import uvicorn

DATABASE_URL = "postgresql://postgres:root@localhost:5432/books"

Base = declarative_base()


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@strawberry.type
class BookType:
    id: int
    title: str
    author: str


@strawberry.input
class BookInput:
    title: str
    author: str


@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> List[BookType]:
        db = next(get_db())
        books = db.query(Book).all()
        return [
            BookType(id=book.id, title=book.title, author=book.author) for book in books
        ]

    @strawberry.field
    def book_by_id(self, id: int) -> Optional[BookType]:
        db = next(get_db())
        book = db.query(Book).filter(Book.id == id).first()
        if book:
            return BookType(id=book.id, title=book.title, author=book.author)
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_book(self, input: BookInput) -> BookType:
        db = next(get_db())
        new_book = Book(title=input.title, author=input.author)
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return BookType(id=new_book.id, title=new_book.title, author=new_book.author)

    @strawberry.mutation
    def update_book(self, id: int, input: BookInput) -> Optional[BookType]:
        db = next(get_db())
        book = db.query(Book).filter(Book.id == id).first()
        if book:
            book.title = input.title
            book.author = input.author
            db.commit()
            db.refresh(book)
            return BookType(id=book.id, title=book.title, author=book.author)
        return None

    @strawberry.mutation
    def delete_book(self, id: int) -> bool:
        db = next(get_db())
        book = db.query(Book).filter(Book.id == id).first()
        if book:
            db.delete(book)
            db.commit()
            return True
        return False


schema = strawberry.Schema(query=Query, mutation=Mutation)

app = FastAPI()

graphql_app: GraphQLRouter = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host="127.0.0.1", port=8000)


"""
mutation {
  createBook(input: { title: "New Book", author: "Author Name" }) {
    id
    title
    author
  }
}

mutation {
  updateBook(id: 1, input: { title: "Updated Title", author: "Updated Author" }) {
    id
    title
    author
  }
}

mutation {
  deleteBook(id: 1)
}

query {
  books {
    id
    title
    author
  }
}

query {
  bookById(id: 1) {
    id
    title
    author
  }
}

"""
