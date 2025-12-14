from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from database import init_db
from api import routers
from dependencies import http_bearer

# Инициализация БД при старте
init_db()

app = FastAPI(
    title="Imageboard API",
    description="API для аналога имиджборда",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)


def custom_openapi():
    """Кастомизация OpenAPI схемы для поддержки JWT в Swagger"""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Imageboard API",
        version="1.0.0",
        description="API для аналога имиджборда. Для авторизации: 1) Вызовите /auth/login для получения JWT токена, 2) Нажмите кнопку 'Authorize' в Swagger UI, 3) Введите токен в формате: Bearer <ваш_токен>",
        routes=app.routes,
    )
    # Добавляем security схему
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите JWT токен, полученный через /auth/login. Формат: Bearer <token> или просто <token>"
        }
    }
    
    # Улучшаем отображение file_url в Swagger
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        if "PostResponse" in openapi_schema["components"]["schemas"]:
            post_schema = openapi_schema["components"]["schemas"]["PostResponse"]
            if "properties" in post_schema and "file_url" in post_schema["properties"]:
                post_schema["properties"]["file_url"]["description"] = (
                    "URL для получения файла. Кликните на ссылку или используйте GET /posts/{id}/file "
                    "для просмотра изображений и видео прямо в Swagger UI."
                )
                post_schema["properties"]["file_url"]["example"] = "http://localhost:8000/posts/1/file"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
for router in routers:
    app.include_router(router)

# Подключение статических файлов (HTML страница)
import os
from pathlib import Path

# Определяем путь к frontend относительно текущего файла
current_dir = Path(__file__).parent
frontend_dir = current_dir.parent / "frontend"  # ../frontend от backend/

# Если frontend не найден относительно backend, пробуем найти в текущей директории
if not frontend_dir.exists():
    frontend_dir = current_dir / "frontend"

try:
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
        print(f"✓ Статические файлы подключены из: {frontend_dir}")
    else:
        print(f"⚠ Директория frontend не найдена: {frontend_dir}")
except Exception as e:
    print(f"⚠ Ошибка подключения статических файлов: {e}")


@app.get("/")
def root():
    """Корневой эндпоинт - возвращает index.html"""
    from fastapi.responses import FileResponse
    
    # Пытаемся найти index.html в разных местах
    possible_paths = [
        frontend_dir / "index.html",
        Path("frontend") / "index.html",
        Path("../frontend") / "index.html",
        Path("./frontend") / "index.html",
    ]
    
    for frontend_path in possible_paths:
        if frontend_path.exists():
            return FileResponse(str(frontend_path))
    
    return {
        "message": "Imageboard API",
        "docs": "/docs",
        "redoc": "/redoc",
        "frontend": "Откройте /static/index.html или настройте путь к frontend"
    }


@app.get("/health")
def health_check():
    """Проверка здоровья приложения"""
    return {"status": "ok"}

