from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Request, Header
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from urllib.parse import quote
from database import get_db
from models import Post, User
from schemas import PostResponse
from dependencies import get_current_user
from file_utils import save_uploaded_file, delete_file, get_file_path

router = APIRouter(prefix="/posts", tags=["posts"])


def add_file_url_to_post(post: Post, request: Request) -> dict:
    """Добавляет file_url к посту для отображения в Swagger"""
    post_dict = {
        "id": post.id,
        "text": post.text,
        "file_path": post.file_path,
        "file_type": post.file_type,
        "file_name": post.file_name,
        "file_url": None,
        "date": post.date,
        "is_deleted": post.is_deleted,
        "upvotes": post.upvotes
    }
    
    # Добавляем URL для файла, если он есть
    if post.file_path:
        base_url = str(request.base_url).rstrip('/')
        post_dict["file_url"] = f"{base_url}/posts/{post.id}/file"
    
    return post_dict


@router.get("", response_model=List[PostResponse])
def get_posts(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    include_deleted: bool = Query(False, description="Включить удалённые посты"),
    db: Session = Depends(get_db)
):
    """Получить список постов"""
    query = db.query(Post)
    
    if not include_deleted:
        query = query.filter(Post.is_deleted == False)
    
    posts = query.order_by(Post.date.desc()).offset(skip).limit(limit).all()
    
    # Добавляем file_url к каждому посту
    return [add_file_url_to_post(post, request) for post in posts]


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    """Получить пост по ID"""
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    # Добавляем file_url для отображения в Swagger
    return add_file_url_to_post(post, request)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    request: Request,
    text: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать новый пост с возможностью загрузки файла"""
    file_path = None
    file_type = None
    file_name = None
    
    # Сохраняем файл, если он загружен
    if file:
        file_path, file_type, file_name = await save_uploaded_file(file)
    
    new_post = Post(
        text=text,
        file_path=file_path,
        file_type=file_type,
        file_name=file_name
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Добавляем file_url для отображения в Swagger
    return add_file_url_to_post(new_post, request)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    request: Request,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить пост (можно обновить текст и/или файл)"""
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    if post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя обновить удалённый пост"
        )
    
    # Обновляем текст, если передан
    if text is not None:
        post.text = text
    
    # Обновляем файл, если загружен новый
    if file:
        # Удаляем старый файл, если он был
        if post.file_path:
            delete_file(post.file_path)
        
        # Сохраняем новый файл
        file_path, file_type, file_name = await save_uploaded_file(file)
        post.file_path = file_path
        post.file_type = file_type
        post.file_name = file_name
    
    db.commit()
    db.refresh(post)
    
    # Добавляем file_url для отображения в Swagger
    return add_file_url_to_post(post, request)


@router.delete("/{post_id}", response_model=PostResponse)
def delete_post(
    post_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить пост (soft delete)"""
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    # Удаляем файл с диска при удалении поста
    if post.file_path:
        delete_file(post.file_path)
    
    post.is_deleted = True
    post.file_path = None
    post.file_type = None
    post.file_name = None
    db.commit()
    db.refresh(post)
    
    # Добавляем file_url (будет None, так как файл удалён)
    return add_file_url_to_post(post, request)


@router.post("/{post_id}/upvote", response_model=PostResponse)
def upvote_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Увеличить количество апвоутов поста"""
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    if post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя апвоутить удалённый пост"
        )
    
    post.upvotes += 1
    db.commit()
    db.refresh(post)
    
    # Добавляем file_url для отображения в Swagger
    return add_file_url_to_post(post, request)


@router.get(
    "/{post_id}/file",
    responses={
        200: {
            "content": {
                "image/jpeg": {},
                "image/png": {},
                "image/gif": {},
                "image/webp": {},
                "video/mp4": {},
                "video/webm": {},
                "video/ogg": {},
                "video/quicktime": {},
                "audio/mpeg": {},
                "audio/ogg": {},
                "audio/wav": {},
                "audio/webm": {},
                "audio/flac": {},
                "audio/x-flac": {},
            },
            "description": "Файл поста. Swagger UI автоматически отобразит изображения и видео. Примечание: FLAC может не воспроизводиться в некоторых браузерах из-за ограничений поддержки формата."
        }
    }
)
def get_post_file(
    post_id: int,
    range_header: Optional[str] = Header(None, alias="Range"),
    db: Session = Depends(get_db)
):
    """
    Получить файл поста
    
    **Для просмотра в Swagger UI:**
    - Изображения (JPEG, PNG, GIF, WebP) будут отображены автоматически
    - Видео (MP4, WebM, OGG, MOV) можно воспроизвести прямо в Swagger UI
    - Аудио файлы (MP3, OGG, WAV, WebM) можно воспроизвести в Swagger UI
    - FLAC файлы могут не воспроизводиться в некоторых браузерах (Chrome, Firefox не поддерживают FLAC в HTML5 audio)
      В этом случае файл можно скачать и воспроизвести во внешнем плеере
    - Или используйте file_url из ответа GET /posts/{id} для прямого доступа
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пост не найден"
        )
    
    if not post.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="У поста нет файла"
        )
    
    file_path = get_file_path(post.file_path)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден на сервере"
        )
    
    # Определяем media_type для правильного Content-Type
    media_type = post.file_type or "application/octet-stream"
    
    # Для изображений, видео и аудио используем inline, чтобы Swagger UI мог их отобразить
    # Для других файлов - attachment (скачивание)
    is_media = (
        media_type.startswith('image/') or 
        media_type.startswith('video/') or 
        media_type.startswith('audio/')
    )
    
    # Формируем имя файла для заголовка
    filename = post.file_name or "file"
    
    if is_media:
        # Получаем размер файла
        file_size = file_path.stat().st_size
        
        # Обработка Range requests для потоковой передачи (важно для аудио/видео)
        if range_header:
            # Парсим Range заголовок (формат: bytes=start-end)
            try:
                range_match = range_header.replace('bytes=', '').split('-')
                start = int(range_match[0]) if range_match[0] else 0
                end = int(range_match[1]) if range_match[1] and range_match[1] else file_size - 1
                
                if start >= file_size or end >= file_size:
                    raise HTTPException(
                        status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                        detail="Range Not Satisfiable"
                    )
                
                # Читаем только нужную часть файла
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    content = f.read(end - start + 1)
                
                # Кодируем имя файла
                try:
                    filename_ascii = filename.encode('ascii', 'ignore').decode('ascii')
                    if not filename_ascii or filename_ascii != filename:
                        filename_encoded = quote(filename, safe='')
                        content_disposition = f'inline; filename*=UTF-8\'\'{filename_encoded}'
                    else:
                        content_disposition = f'inline; filename="{filename_ascii}"'
                except:
                    content_disposition = 'inline; filename="file"'
                
                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(len(content)),
                    "Content-Disposition": content_disposition
                }
                
                return Response(
                    content=content,
                    media_type=media_type,
                    status_code=status.HTTP_206_PARTIAL_CONTENT,
                    headers=headers
                )
            except (ValueError, IndexError):
                # Если Range заголовок некорректный, возвращаем весь файл
                pass
        
        # Обычный запрос - возвращаем весь файл
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Кодируем имя файла для заголовка согласно RFC 2231
        try:
            filename_ascii = filename.encode('ascii', 'ignore').decode('ascii')
            if not filename_ascii or filename_ascii != filename:
                filename_encoded = quote(filename, safe='')
                content_disposition = f'inline; filename*=UTF-8\'\'{filename_encoded}'
            else:
                content_disposition = f'inline; filename="{filename_ascii}"'
        except:
            content_disposition = 'inline; filename="file"'
        
        # Заголовки для медиа-файлов
        headers = {
            "Content-Disposition": content_disposition,
            "Accept-Ranges": "bytes",  # Поддержка частичных запросов для потоковой передачи
            "Content-Length": str(len(content))
        }
        
        # Для аудио файлов добавляем дополнительные заголовки
        if media_type.startswith('audio/'):
            headers["Cache-Control"] = "public, max-age=3600"
        
        return Response(
            content=content,
            media_type=media_type,
            headers=headers
        )
    else:
        # Для других файлов - attachment (скачивание)
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )

