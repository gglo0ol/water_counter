#!/usr/bin/env python3



from models.database import engine
from models.entities import Base
from ui.console_ui import ConsoleUI

def init_database():
    """Инициализация базы данных"""
    print("🔧 Инициализация базы данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")

def main():
    """Главная функция приложения"""
    try:
        # Инициализируем базу данных
        init_database()
        
        # Запускаем консольный интерфейс
        ui = ConsoleUI()
        ui.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Приложение завершено пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("Попробуйте перезапустить приложение")

if __name__ == "__main__":
    main()
