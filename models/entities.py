from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Counter(Base):
    """Модель счетчика воды"""
    __tablename__ = "counters"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), unique=True, index=True, nullable=False)
    water_type = Column(String(20), nullable=False)  # "hot" или "cold"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с показаниями
    readings = relationship("Reading", back_populates="counter")

class Reading(Base):
    """Модель показаний счетчика"""
    __tablename__ = "readings"
    
    id = Column(Integer, primary_key=True, index=True)
    counter_id = Column(Integer, ForeignKey("counters.id"), nullable=False)
    value = Column(Integer, nullable=False)  # Показание в м³
    reading_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь со счетчиком
    counter = relationship("Counter", back_populates="readings")

class Tariff(Base):
    """Модель тарифа на воду"""
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(String(20), nullable=False)  # "cold_water", "hot_water", "wastewater"
    price_per_cubic_meter = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # None означает действующий тариф
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    """Модель платежа"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Потребление холодной воды
    cold_water_consumption = Column(Integer, nullable=False)  # в м³
    cold_water_amount = Column(Float, nullable=False)
    
    # Подогрев воды (горячая вода)
    hot_water_consumption = Column(Integer, nullable=False)  # в м³
    hot_water_amount = Column(Float, nullable=False)
    
    # Утилизация воды (общий объем)
    wastewater_consumption = Column(Integer, nullable=False)  # в м³ (холодная + горячая)
    wastewater_amount = Column(Float, nullable=False)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
