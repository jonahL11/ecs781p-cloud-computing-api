DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS user_favorites;
DROP TABLE IF EXISTS papers_authors;
--delete the junction tables first
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS papers;
DROP TABLE IF EXISTS authors;
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    fullname VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL --need to store hashed password
);
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name VARCHAR(255) NOT NULL UNIQUE
);
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    abstract VARCHAR(255) NOT NULL,
    publication_date VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL
);
CREATE TABLE user_favorites (
    paper_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (paper_id, user_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_name VARCHAR(255) NOT NULL,
    paper_count INTEGER NOT NULL DEFAULT 0,
    citation_count INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE papers_authors (
    paper_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    author_order INTEGER NOT NULL,
    PRIMARY KEY (paper_id, author_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (author_id) REFERENCES authors(id)

);