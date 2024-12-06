import os
import strawberry
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
from strawberry.fastapi import GraphQLRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
# # # DATABASE SETUP
DATABASE_URL = os.environ.get("DATABASE_URL")
# DATABASE_URL = "postgresql://postgres:root@localhost:5432/books"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)


init_db()


# # # GRAPHQL SETUP
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
class StandardResponse:
    success: bool
    message: str
    data: Optional[BookType] = None
    data_list: Optional[List[BookType]] = None


@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> StandardResponse:
        try:
            db = next(get_db())
            books = db.query(Book).all()
            return StandardResponse(
                success=True,
                message="Books fetched successfully",
                data_list=[
                    BookType(id=book.id, title=book.title, author=book.author)
                    for book in books
                ],
            )
        except Exception as e:
            return StandardResponse(success=False, message=f"Error: {str(e)}")

    @strawberry.field
    def book_by_id(self, id: int) -> StandardResponse:
        try:
            db = next(get_db())
            book = db.query(Book).filter(Book.id == id).first()
            if book:
                return StandardResponse(
                    success=True,
                    message="Book fetched successfully",
                    data=BookType(id=book.id, title=book.title, author=book.author),
                )
            return StandardResponse(success=False, message="Book not found")
        except Exception as e:
            return StandardResponse(success=False, message=f"Error: {str(e)}")


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_book(self, input: BookInput) -> StandardResponse:
        try:
            db = next(get_db())
            new_book = Book(title=input.title, author=input.author)
            db.add(new_book)
            db.commit()
            db.refresh(new_book)
            return StandardResponse(
                success=True,
                message="Book created successfully",
                data=BookType(
                    id=new_book.id, title=new_book.title, author=new_book.author
                ),
            )
        except Exception as e:
            return StandardResponse(success=False, message=f"Error: {str(e)}")

    @strawberry.mutation
    def update_book(self, id: int, input: BookInput) -> StandardResponse:
        try:
            db = next(get_db())
            book = db.query(Book).filter(Book.id == id).first()
            if book:
                book.title = input.title
                book.author = input.author
                db.commit()
                db.refresh(book)
                return StandardResponse(
                    success=True,
                    message="Book updated successfully",
                    data=BookType(id=book.id, title=book.title, author=book.author),
                )
            return StandardResponse(success=False, message="Book not found")
        except Exception as e:
            return StandardResponse(success=False, message=f"Error: {str(e)}")

    @strawberry.mutation
    def delete_book(self, id: int) -> StandardResponse:
        try:
            db = next(get_db())
            book = db.query(Book).filter(Book.id == id).first()
            if book:
                db.delete(book)
                db.commit()
                return StandardResponse(
                    success=True, message="Book deleted successfully"
                )
            return StandardResponse(success=False, message="Book not found")
        except Exception as e:
            return StandardResponse(success=False, message=f"Error: {str(e)}")


schema = strawberry.Schema(query=Query, mutation=Mutation)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graphql_app: GraphQLRouter = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
