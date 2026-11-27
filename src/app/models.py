from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    fullname = db.Column(db.String(255), nullable=False)
    # Needs to be hashed + salted
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
