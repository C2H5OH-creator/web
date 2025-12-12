from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from database import init_db
from routers import auth, posts, users, metadata
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
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(users.router)
app.include_router(metadata.router)

# Подключение статических файлов (HTML страница)
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except:
    pass  # Если директория не существует, пропускаем


@app.get("/")
def root():
    """Корневой эндпоинт"""
    return {
        "message": "Imageboard API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Проверка здоровья приложения"""
    return {"status": "ok"}

