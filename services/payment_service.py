from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from models.entities import Payment, Tariff
from models.schemas import PaymentCreate, Payment as PaymentSchema, PaymentCalculation
from .reading_service import ReadingService

DEFAULT_TARIFFS = [
            ("cold_water", 68.02),      # 68.02 руб за м³ холодной воды
            ("hot_water", 166.8),      # 166.8 руб за м³ горячей воды (подогрев)
            ("wastewater", 62.00),      # 62.00 руб за м³ утилизации
        ]
        

class PaymentService:
    """Сервис для расчета платежей"""
    
    def __init__(self, db: Session):
        self.db = db
        self.reading_service = ReadingService(db)
    
    def get_current_tariff(self, service_type: str) -> Optional[Tariff]:
        """Получение действующего тарифа для типа услуги"""
        return self.db.query(Tariff)\
            .filter(Tariff.service_type == service_type)\
            .filter((Tariff.end_date.is_(None)) | (Tariff.end_date > datetime.now()))\
            .order_by(desc(Tariff.start_date))\
            .first()
    
    def create_tariff(self, service_type: str, price_per_cubic_meter: float, start_date: datetime) -> Tariff:
        """Создание нового тарифа"""
        # Закрываем предыдущий тариф
        current_tariff = self.get_current_tariff(service_type)
        if current_tariff:
            current_tariff.end_date = start_date
            self.db.commit()
        
        # Создаем новый тариф
        new_tariff = Tariff(
            service_type=service_type,
            price_per_cubic_meter=price_per_cubic_meter,
            start_date=start_date
        )
        self.db.add(new_tariff)
        self.db.commit()
        self.db.refresh(new_tariff)
        return new_tariff
    
    def calculate_monthly_payment(self, year: int, month: int) -> PaymentCalculation:
        """Расчет платежа за месяц"""
        # Определяем период
        if month == 12:
            period_start = datetime(year, month, 1)
            period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            period_start = datetime(year, month, 1)
            period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Получаем потребление за месяц
        consumption = self.reading_service.get_monthly_consumption(year, month)
        
        # Получаем действующие тарифы
        hot_water_tariff = self.get_current_tariff("hot_water")
        cold_water_tariff = self.get_current_tariff("cold_water")
        wastewater_tariff = self.get_current_tariff("wastewater")
        
        if not hot_water_tariff or not cold_water_tariff or not wastewater_tariff:
            raise ValueError("Не установлены тарифы для всех услуг")
        
        # Рассчитываем потребление утилизации (общий объем)
        wastewater_consumption = consumption["hot"] + consumption["cold"]
        
        # Рассчитываем суммы
        hot_water_amount = consumption["hot"] * hot_water_tariff.price_per_cubic_meter
        cold_water_amount = consumption["cold"] * cold_water_tariff.price_per_cubic_meter
        wastewater_amount = wastewater_consumption * wastewater_tariff.price_per_cubic_meter
        total_amount = hot_water_amount + cold_water_amount + wastewater_amount
        
        return PaymentCalculation(
            period_start=period_start,
            period_end=period_end,
            hot_water_consumption=consumption["hot"],
            cold_water_consumption=consumption["cold"],
            wastewater_consumption=wastewater_consumption,
            hot_water_rate=hot_water_tariff.price_per_cubic_meter,
            cold_water_rate=cold_water_tariff.price_per_cubic_meter,
            wastewater_rate=wastewater_tariff.price_per_cubic_meter,
            total_amount=total_amount
        )
    
    def create_payment(self, calculation: PaymentCalculation, notes: str = None) -> Payment:
        """Создание записи о платеже"""
        payment = Payment(
            period_start=calculation.period_start,
            period_end=calculation.period_end,
            total_amount=calculation.total_amount,
            hot_water_amount=calculation.hot_water_consumption * calculation.hot_water_rate,
            cold_water_amount=calculation.cold_water_consumption * calculation.cold_water_rate,
            wastewater_amount=calculation.wastewater_consumption * calculation.wastewater_rate,
            hot_water_consumption=calculation.hot_water_consumption,
            cold_water_consumption=calculation.cold_water_consumption,
            wastewater_consumption=calculation.wastewater_consumption,
            notes=notes
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_payment(self, payment_id: int) -> Optional[Payment]:
        """Получение платежа по ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()
    
    def get_all_payments(self) -> List[Payment]:
        """Получение всех платежей"""
        return self.db.query(Payment).order_by(desc(Payment.calculated_at)).all()
    
    def get_payments_by_year(self, year: int) -> List[Payment]:
        """Получение платежей за год"""
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        return self.db.query(Payment)\
            .filter(Payment.period_start >= start_date, Payment.period_start <= end_date)\
            .order_by(Payment.period_start)\
            .all()
    
    def get_payment_summary(self, year: int) -> Dict:
        """Получение сводки платежей за год"""
        payments = self.get_payments_by_year(year)
        
        total_amount = sum(p.total_amount for p in payments)
        total_hot_water = sum(p.hot_water_consumption for p in payments)
        total_cold_water = sum(p.cold_water_consumption for p in payments)
        
        return {
            "year": year,
            "total_payments": len(payments),
            "total_amount": total_amount,
            "total_hot_water_consumption": total_hot_water,
            "total_cold_water_consumption": total_cold_water,
            "average_monthly_amount": total_amount / 12 if payments else 0
        }
    
    def initialize_default_tariffs(self) -> List[Tariff]:
        """Инициализация тарифов по умолчанию"""
        
        created_tariffs = []
        for service_type, price in DEFAULT_TARIFFS:
            # Проверяем, есть ли уже действующий тариф
            existing_tariff = self.get_current_tariff(service_type)
            if not existing_tariff:
                new_tariff = self.create_tariff(service_type, price, datetime.now())
                created_tariffs.append(new_tariff)
        
        return created_tariffs
