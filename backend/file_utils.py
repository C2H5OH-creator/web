import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from typing import Optional, Tuple

# Директория для хранения загруженных файлов
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Разрешённые типы файлов
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/ogg", "video/quicktime"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/ogg", "audio/wav", "audio/webm", "audio/flac", "audio/x-flac"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_AUDIO_TYPES

# Максимальный размер файла (50 МБ)
MAX_FILE_SIZE = 50 * 1024 * 1024


def validate_file_type(file: UploadFile) -> bool:
    """Проверка типа файла"""
    if file.content_type not in ALLOWED_TYPES:
        return False
    return True


def get_file_category(content_type: str) -> str:
    """Определяет категорию файла"""
    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"
    elif content_type in ALLOWED_VIDEO_TYPES:
        return "video"
    elif content_type in ALLOWED_AUDIO_TYPES:
        return "audio"
    return "unknown"


def generate_file_path(file: UploadFile) -> Tuple[str, str]:
    """
    Генерирует уникальный путь для файла
    Возвращает: (путь к файлу, имя файла)
    """
    # Получаем расширение из оригинального имени или content_type
    original_filename = file.filename or "file"
    file_ext = Path(original_filename).suffix
    
    # Если расширения нет, пытаемся определить по content_type
    if not file_ext:
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "video/ogg": ".ogv",
            "video/quicktime": ".mov",
            "audio/mpeg": ".mp3",
            "audio/ogg": ".ogg",
            "audio/wav": ".wav",
            "audio/webm": ".weba",
            "audio/flac": ".flac",
            "audio/x-flac": ".flac",
        }
        file_ext = ext_map.get(file.content_type, "")
    
    # Генерируем уникальное имя файла
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}{file_ext}"
    
    # Создаём поддиректорию по категории файла
    category = get_file_category(file.content_type)
    category_dir = UPLOAD_DIR / category
    category_dir.mkdir(exist_ok=True)
    
    file_path = category_dir / filename
    
    # Возвращаем относительный путь от корня проекта (для хранения в БД)
    # Путь будет вида: uploads/image/uuid.jpg
    relative_path = str(file_path)
    return relative_path, original_filename


async def save_uploaded_file(file: UploadFile) -> Tuple[str, str, str]:
    """
    Сохраняет загруженный файл
    Возвращает: (путь к файлу, тип файла, оригинальное имя)
    """
    # Проверка типа файла
    if not validate_file_type(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый тип файла. Разрешены: изображения (JPEG, PNG, GIF, WebP), видео (MP4, WebM, OGG, MOV), аудио (MP3, OGG, WAV, WebM, FLAC)"
        )
    
    # Генерируем путь
    file_path, original_filename = generate_file_path(file)
    
    # Читаем и сохраняем файл
    content = await file.read()
    
    # Проверка размера
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE / (1024 * 1024):.0f} МБ"
        )
    
    # Сохраняем файл
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path, file.content_type, original_filename


def delete_file(file_path: str) -> bool:
    """Удаляет файл с диска"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False


def get_file_path(post_file_path: Optional[str]) -> Optional[Path]:
    """Возвращает Path объект для файла поста"""
    if not post_file_path:
        return None
    return Path(post_file_path)

