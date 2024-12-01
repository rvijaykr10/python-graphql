CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL
);

INSERT INTO books (title, author)
VALUES 
    ('The Catcher in the Rye', 'J.D. Salinger'),
    ('To Kill a Mockingbird', 'Harper Lee'),
    ('1984', 'George Orwell'),
    ('The Great Gatsby', 'F. Scott Fitzgerald'),
    ('Moby-Dick', 'Herman Melville');
