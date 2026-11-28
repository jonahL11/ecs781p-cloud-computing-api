from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class User(db.Model):
    """
    SQLAlchemy ORM User model
    Attributes:
        id: primary key, autincremented integer
        email: string
        fullname: string
        password: string
    Related to UserRoles and UserFavorites
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    fullname: Mapped[str] = mapped_column(db.String(255), nullable=False)
    # Needs to be hashed + salted
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)

    user_roles: Mapped[list[UserRoles]] = relationship(back_populates="users")
    user_favorites: Mapped[list[UserFavorites]] = relationship(back_populates="users")

    def __repr__(self):
        return f"<User {self.email}>"


class Roles(db.Model):
    """
    SQLAlchemy ORM Role model used for authorization
    Attributes:
        id: primary key, autincremented integer
        role_name: string
    Related to UserRoles
    """

    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)

    user_roles: Mapped[list[UserRoles]] = relationship(back_populates="roles")

    def __repr__(self):
        return f"<Role {self.role_name}>"


class UserRoles(db.Model):
    """
    SQLAlchemy ORM User-Role connector model for authorization
    Attributes:
        id: primary key, autincremented integer
        user_id: foreign key integer
        role_id: foreign key integer
    Related to Users and Roles
    """

    __tablename__ = "user_roles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # We want a user to have one role and one role only
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), unique=True
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", onupdate="CASCADE"))

    users: Mapped[User] = relationship(back_populates="user_roles")
    roles: Mapped[Roles] = relationship(back_populates="user_roles")

    def __repr__(self):
        return f"<UserRole {self.id}>"


class Papers(db.Model):
    """
    SQLAlchemy ORM Paper model
    Attributes:
        id: primary key, autincremented integer
        title: string
        abstract: string
        publication_date: string
        doi: string (url)
    Related to PapersAuthors and UsersFavorites
    """

    __tablename__ = "papers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False)
    abstract: Mapped[str] = mapped_column(db.String(255), nullable=False)
    # could also be explicit date with db.Date
    publication_date: Mapped[str] = mapped_column(db.String(255), nullable=False)
    # doi instead of url
    doi: Mapped[str] = mapped_column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Paper {self.id}>"

    papers_authors: Mapped[list[PapersAuthors]] = relationship(back_populates="papers")
    user_favorites: Mapped[list[UserFavorites]] = relationship(back_populates="papers")


class Authors(db.Model):
    """
    SQLAlchemy ORM Author model
    Attributes:
        id: primary key, autincremented integer
        author_name: string
        paper_count: integer, default 0
        citation_count: integer, default 0
    Related to PapersAuthors
    """

    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author_name: Mapped[str] = mapped_column(
        db.String(255), unique=True, nullable=False
    )
    paper_count: Mapped[int] = mapped_column(db.Integer, default=0)
    citation_count: Mapped[int] = mapped_column(db.Integer, default=0)

    def __repr__(self):
        return f"<Author {self.author_name}>"

    papers_authors: Mapped[list[PapersAuthors]] = relationship(back_populates="authors")


class PapersAuthors(db.Model):
    """
    SQLAlchemy ORM Paper Authors connector model
    Attributes:
        author_id: primary_key, foreign_key, autoincremented integer
        paper_id: primary_key, foreign_key, autoincremented integer
        author_order: id, in which position the author appears in the author list
    Related to Papers and Authors
    """

    __tablename__ = "papers_authors"
    author_id: Mapped[int] = mapped_column(
        ForeignKey("authors.id", onupdate="CASCADE"),
        primary_key=True,
    )
    author_order: Mapped[int] = mapped_column(db.Integer)
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", onupdate="CASCADE"),
        primary_key=True,
    )

    papers: Mapped[Papers] = relationship(back_populates="papers_authors")
    authors: Mapped[Authors] = relationship(back_populates="papers_authors")

    def __repr__(self):
        return f"<PapersAuthor author_id: {self.author_id}, paper_id: {self.paper_id}>"


class UserFavorites(db.Model):
    """
    SQLAlchemy ORM User Favorites (Papers) connector model
    Attributes:
        paper_id: primary_key, foreign_key, autoincremented integer
        user_id: primary_key, foreign_key, autoincremented integer
    Related to Users and Papers
    """

    __tablename__ = "user_favorites"
    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id", onupdate="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE"), primary_key=True
    )

    papers: Mapped[Papers] = relationship(back_populates="user_favorites")
    users: Mapped[User] = relationship(back_populates="user_favorites")

    def __repr__(self):
        return f"<UserFavorites user_id: {self.user_id}, paper_id: {self.paper_id}>"
