from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # Хэшированный пароль
    nick = Column(String(100), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)  # Путь к файлу на сервере
    file_type = Column(String(50), nullable=True)  # MIME type файла (image/jpeg, video/mp4, audio/mpeg, image/gif)
    file_name = Column(String(255), nullable=True)  # Оригинальное имя файла
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    upvotes = Column(Integer, default=0, nullable=False)

