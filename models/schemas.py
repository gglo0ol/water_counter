from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

class CounterBase(BaseModel):
    """Базовая схема счетчика"""
    number: str = Field(..., min_length=1, max_length=50)
    water_type: str = Field(..., pattern="^(hot|cold)$")
    description: Optional[str] = None

class CounterCreate(CounterBase):
    """Схема для создания счетчика"""
    pass

class Counter(CounterBase):
    """Схема счетчика с ID"""
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class ReadingBase(BaseModel):
    """Базовая схема показаний"""
    counter_id: int
    value: int = Field(..., ge=0)  # Показание должно быть >= 0
    reading_date: datetime

class ReadingCreate(ReadingBase):
    """Схема для создания показаний"""
    pass

class Reading(ReadingBase):
    """Схема показаний с ID"""
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class TariffBase(BaseModel):
    """Базовая схема тарифа"""
    service_type: str = Field(..., pattern="^(cold_water|hot_water|wastewater)$")
    price_per_cubic_meter: float = Field(..., gt=0)
    start_date: datetime
    end_date: Optional[datetime] = None

class TariffCreate(TariffBase):
    """Схема для создания тарифа"""
    pass

class Tariff(TariffBase):
    """Схема тарифа с ID"""
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class PaymentBase(BaseModel):
    """Базовая схема платежа"""
    period_start: datetime
    period_end: datetime
    total_amount: float = Field(..., ge=0)
    
    # Потребление холодной воды
    cold_water_consumption: int = Field(..., ge=0)
    cold_water_amount: float = Field(..., ge=0)
    
    # Подогрев воды (горячая вода)
    hot_water_consumption: int = Field(..., ge=0)
    hot_water_amount: float = Field(..., ge=0)
    
    # Утилизация воды (общий объем)
    wastewater_consumption: int = Field(..., ge=0)
    wastewater_amount: float = Field(..., ge=0)
    
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    """Схема для создания платежа"""
    pass

class Payment(PaymentBase):
    """Схема платежа с ID"""
    id: int
    calculated_at: datetime
    
    model_config = {"from_attributes": True}

class MonthlyReadings(BaseModel):
    """Схема для ввода месячных показаний"""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    readings: List[ReadingCreate]

class PaymentCalculation(BaseModel):
    """Схема для расчета платежа"""
    period_start: datetime
    period_end: datetime
    hot_water_consumption: int = Field(..., ge=0)
    cold_water_consumption: int = Field(..., ge=0)
    wastewater_consumption: int = Field(..., ge=0)
    hot_water_rate: float = Field(..., gt=0)
    cold_water_rate: float = Field(..., gt=0)
    wastewater_rate: float = Field(..., gt=0)
    total_amount: float = Field(..., ge=0)
