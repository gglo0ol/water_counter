from sqlalchemy.orm import Session
from typing import List, Optional
from models.entities import Counter
from models.schemas import CounterCreate, Counter as CounterSchema

class CounterService:
    """Сервис для работы со счетчиками"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_counter(self, counter: CounterCreate) -> Counter:
        """Создание нового счетчика"""
        db_counter = Counter(
            number=counter.number,
            water_type=counter.water_type,
            description=counter.description
        )
        self.db.add(db_counter)
        self.db.commit()
        self.db.refresh(db_counter)
        return db_counter
    
    def get_counter(self, counter_id: int) -> Optional[Counter]:
        """Получение счетчика по ID"""
        return self.db.query(Counter).filter(Counter.id == counter_id).first()
    
    def get_counter_by_number(self, number: str) -> Optional[Counter]:
        """Получение счетчика по номеру"""
        return self.db.query(Counter).filter(Counter.number == number).first()
    
    def get_all_counters(self) -> List[Counter]:
        """Получение всех счетчиков"""
        return self.db.query(Counter).all()
    
    def get_counters_by_type(self, water_type: str) -> List[Counter]:
        """Получение счетчиков по типу воды"""
        return self.db.query(Counter).filter(Counter.water_type == water_type).all()
    
    def update_counter(self, counter_id: int, counter: CounterCreate) -> Optional[Counter]:
        """Обновление счетчика"""
        db_counter = self.get_counter(counter_id)
        if db_counter:
            db_counter.number = counter.number
            db_counter.water_type = counter.water_type
            db_counter.description = counter.description
            self.db.commit()
            self.db.refresh(db_counter)
        return db_counter
    
    def delete_counter(self, counter_id: int) -> bool:
        """Удаление счетчика"""
        db_counter = self.get_counter(counter_id)
        if db_counter:
            self.db.delete(db_counter)
            self.db.commit()
            return True
        return False
    
    def initialize_default_counters(self) -> List[Counter]:
        """Инициализация счетчиков по умолчанию (4 счетчика)"""
        default_counters = [
            CounterCreate(number="ГВ-1", water_type="hot", description="Горячая вода счетчик 1"),
            CounterCreate(number="ГВ-2", water_type="hot", description="Горячая вода счетчик 2"),
            CounterCreate(number="ХВ-1", water_type="cold", description="Холодная вода счетчик 1"),
            CounterCreate(number="ХВ-2", water_type="cold", description="Холодная вода счетчик 2"),
        ]
        
        created_counters = []
        for counter_data in default_counters:
            # Проверяем, существует ли уже счетчик с таким номером
            existing = self.get_counter_by_number(counter_data.number)
            if not existing:
                created_counter = self.create_counter(counter_data)
                created_counters.append(created_counter)
        
        return created_counters
