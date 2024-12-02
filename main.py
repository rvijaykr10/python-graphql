import strawberry
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
from strawberry.fastapi import GraphQLRouter
from fastapi.middleware.cors import CORSMiddleware

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


# GraphQL types
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
    data: Optional[BookType] = None  # For single book responses
    data_list: Optional[List[BookType]] = None  # For list responses


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
    allow_origins=["http://localhost:5173"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

graphql_app: GraphQLRouter = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
