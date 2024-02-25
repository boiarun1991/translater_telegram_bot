import sqlalchemy as sq
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    id = sq.Column(sq.Integer, primary_key=True)
    id_telegram = sq.Column(sq.String, unique=True)
    name = sq.Column(sq.String(length=60), unique=True)


class Lexicon(Base):
    __tablename__ = 'lexicon'
    id = sq.Column(sq.Integer, primary_key=True)
    id_user = sq.Column(sq.String, sq.ForeignKey('users.id_telegram'))
    eng_word = sq.Column(sq.String(length=40))
    rus_word = sq.Column(sq.String(length=40))


class User_words(Base):
    __tablename__ = 'user_words'
    id = sq.Column(sq.Integer, primary_key=True)
    id_user = sq.Column(sq.String, sq.ForeignKey('users.id_telegram'))
    id_lexicon = sq.Column(sq.Integer, sq.ForeignKey('lexicon.id'))
    status = sq.Column(sq.Boolean)
    UniqueConstraint('id_user', 'id_lexicon', name='unique_user_words')
    user = relationship('Users', backref='user_words')
    lexicon = relationship('Lexicon', backref='user_words')


def create_tables(engine):
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
