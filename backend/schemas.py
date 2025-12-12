from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


# User Schemas
class UserCreate(BaseModel):
    login: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=72)
    nick: str = Field(..., min_length=1, max_length=100)
    is_admin: bool = False

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        # Bcrypt ограничение: 72 байта максимум
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Пароль не может быть длиннее 72 байт')
        return v


class UserLogin(BaseModel):
    login: str
    password: str = Field(..., max_length=72)


class UserResponse(BaseModel):
    id: int
    login: str
    nick: str
    is_admin: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nick: Optional[str] = None
    is_admin: Optional[bool] = None


# Post Schemas
class PostCreate(BaseModel):
    text: str
    # Файл загружается отдельно через multipart/form-data


class PostUpdate(BaseModel):
    text: Optional[str] = None
    # Файл можно обновить через отдельный эндпоинт


class PostResponse(BaseModel):
    id: int
    text: str
    file_path: Optional[str] = None  # Путь к файлу (внутренний)
    file_type: Optional[str] = None  # MIME type файла
    file_name: Optional[str] = None  # Оригинальное имя файла
    file_url: Optional[str] = None  # URL для получения файла (кликните для просмотра в Swagger)
    date: datetime
    is_deleted: bool
    upvotes: int

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    login: Optional[str] = None

