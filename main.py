import strawberry
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
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


@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> List[BookType]:
        db = next(get_db())
        books = db.query(Book).all()
        return [
            BookType(id=book.id, title=book.title, author=book.author) for book in books
        ]


schema = strawberry.Schema(query=Query)

app = FastAPI()

graphql_app: GraphQLRouter = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host="127.0.0.1", port=8000)
