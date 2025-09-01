from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Tuple
from datetime import datetime, date
from models.entities import Reading, Counter
from models.schemas import ReadingCreate, Reading as ReadingSchema

class ReadingService:
    """Сервис для работы с показаниями счетчиков"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_reading(self, reading: ReadingCreate) -> Reading:
        """Создание нового показания"""
        db_reading = Reading(
            counter_id=reading.counter_id,
            value=reading.value,
            reading_date=reading.reading_date
        )
        self.db.add(db_reading)
        self.db.commit()
        self.db.refresh(db_reading)
        return db_reading
    
    def get_reading(self, reading_id: int) -> Optional[Reading]:
        """Получение показания по ID"""
        return self.db.query(Reading).filter(Reading.id == reading_id).first()
    
    def get_readings_by_counter(self, counter_id: int, limit: int = 10) -> List[Reading]:
        """Получение последних показаний для счетчика"""
        return self.db.query(Reading)\
            .filter(Reading.counter_id == counter_id)\
            .order_by(desc(Reading.reading_date))\
            .limit(limit)\
            .all()
    
    def get_latest_reading_by_counter(self, counter_id: int) -> Optional[Reading]:
        """Получение последнего показания для счетчика"""
        return self.db.query(Reading)\
            .filter(Reading.counter_id == counter_id)\
            .order_by(desc(Reading.reading_date))\
            .first()
    
    def get_readings_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Reading]:
        """Получение показаний за период"""
        return self.db.query(Reading)\
            .filter(Reading.reading_date >= start_date, Reading.reading_date <= end_date)\
            .order_by(Reading.reading_date)\
            .all()
    
    def get_monthly_consumption(self, year: int, month: int) -> Dict[str, int]:
        """Расчет потребления как разница двух последних показаний по каждому счетчику"""
        # Получаем все счетчики
        counters = self.db.query(Counter).all()
        
        consumption = {"hot": 0, "cold": 0}
        
        for counter in counters:
            # Берем два последних показания по дате
            last_two = self.db.query(Reading)\
                .filter(Reading.counter_id == counter.id)\
                .order_by(desc(Reading.reading_date))\
                .limit(2)\
                .all()

            if len(last_two) == 2:
                last_reading, previous_reading = last_two[0], last_two[1]
                diff = last_reading.value - previous_reading.value
                if diff >= 0:
                    consumption[counter.water_type] += diff
                else:
                    print(f"⚠️ Внимание: Показания счетчика {counter.number} уменьшились. Проверьте данные.")
            else:
                print(f"⚠️ Внимание: Для счетчика {counter.number} недостаточно данных (нужно минимум два показания)")
        
        return consumption
    
    def get_latest_reading_by_date(self, counter_id: int, target_date: datetime) -> Optional[Reading]:
        """Получение последнего показания до указанной даты"""
        return self.db.query(Reading)\
            .filter(Reading.counter_id == counter_id, Reading.reading_date <= target_date)\
            .order_by(desc(Reading.reading_date))\
            .first()
    
    def validate_reading(self, counter_id: int, value: int, reading_date: datetime) -> Tuple[bool, str]:
        """Валидация показания"""
        # Получаем последнее показание для этого счетчика
        latest_reading = self.get_latest_reading_by_counter(counter_id)
        
        if latest_reading:
            # Проверяем, что новое показание больше предыдущего
            if value < latest_reading.value:
                return False, f"Новое показание ({value}) меньше предыдущего ({latest_reading.value})"
            
            # Проверяем, что дата показания не раньше предыдущего
            if reading_date < latest_reading.reading_date:
                return False, f"Дата показания ({reading_date}) раньше предыдущего ({latest_reading.reading_date})"
        
        return True, "OK"
    
    def get_consumption_for_period(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Расчет потребления за период"""
        counters = self.db.query(Counter).all()
        consumption = {"hot": 0, "cold": 0}
        
        for counter in counters:
            start_reading = self.get_latest_reading_by_date(counter.id, start_date)
            end_reading = self.get_latest_reading_by_date(counter.id, end_date)
            
            if start_reading and end_reading:
                diff = end_reading.value - start_reading.value
                if diff >= 0:
                    consumption[counter.water_type] += diff
        
        return consumption
