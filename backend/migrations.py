"""
Скрипт миграции для обновления структуры таблицы posts
"""
from sqlalchemy import text
from database import engine


def migrate_posts_table():
    """Миграция таблицы posts: переименование file в file_path и добавление новых полей"""
    try:
        with engine.begin() as conn:  # begin() автоматически делает commit
            # Проверяем, существует ли таблица posts
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'posts'
                )
            """))
            
            if not result.scalar():
                print("Таблица posts не найдена. Будет создана автоматически.")
                return
            
            # Проверяем, существует ли старая колонка file
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'posts' AND column_name = 'file'
            """))
            
            if result.fetchone():
                print("Найдена старая структура таблицы. Выполняется миграция...")
                
                # Переименовываем file в file_path
                conn.execute(text("ALTER TABLE posts RENAME COLUMN file TO file_path"))
                print("✓ Колонка 'file' переименована в 'file_path'")
            
            # Добавляем новые колонки, если их нет
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'posts' AND column_name = 'file_type'
            """))
            
            if not result.fetchone():
                conn.execute(text("ALTER TABLE posts ADD COLUMN file_type VARCHAR(50)"))
                print("✓ Добавлена колонка 'file_type'")
            
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'posts' AND column_name = 'file_name'
            """))
            
            if not result.fetchone():
                conn.execute(text("ALTER TABLE posts ADD COLUMN file_name VARCHAR(255)"))
                print("✓ Добавлена колонка 'file_name'")
            
            print("Миграция завершена успешно!")
            
    except Exception as e:
        print(f"Ошибка при выполнении миграции: {e}")
        # Не поднимаем исключение, чтобы приложение могло запуститься


if __name__ == "__main__":
    migrate_posts_table()

