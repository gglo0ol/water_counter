from datetime import datetime, date
from typing import List
from sqlalchemy.orm import Session
from models.database import get_db
from models.entities import Counter, Reading, Payment, Tariff
from services.counter_service import CounterService
from services.reading_service import ReadingService
from services.payment_service import PaymentService
from models.schemas import ReadingCreate, CounterCreate

class ConsoleUI:
    """Консольный интерфейс для приложения"""
    
    def __init__(self):
        self.db = next(get_db())
        self.counter_service = CounterService(self.db)
        self.reading_service = ReadingService(self.db)
        self.payment_service = PaymentService(self.db)
    
    def show_main_menu(self):
        """Отображение главного меню"""
        print("\n" + "="*50)
        print("🌊 WATER COUNTER - Система учета показаний счетчиков")
        print("="*50)
        print("1. Ввести показания счетчиков")
        print("2. Просмотреть счетчики")
        print("3. Просмотреть историю показаний")
        print("4. Рассчитать платеж за месяц")
        print("5. Просмотреть историю платежей")
        print("6. Управление тарифами")
        print("7. Управление счетчиками")
        print("8. Инициализация системы")
        print("0. Выход")
        print("-"*50)
    
    def input_readings(self):
        """Ввод показаний счетчиков"""
        print("\n📊 ВВОД ПОКАЗАНИЙ СЧЕТЧИКОВ")
        print("-"*30)
        
        # Получаем все счетчики
        counters = self.counter_service.get_all_counters()
        if not counters:
            print("❌ Счетчики не найдены. Сначала инициализируйте систему.")
            return
        
        # Запрашиваем дату показаний
        try:
            current_date = datetime.now()
            default_date_str = current_date.strftime("%d.%m.%Y")
            date_str = input(f"Введите дату показаний (ДД.ММ.ГГГГ, по умолчанию {default_date_str}): ").strip()
            if date_str:
                reading_date = datetime.strptime(date_str, "%d.%m.%Y")
            else:
                reading_date = current_date
        except ValueError:
            print("❌ Неверный формат даты. Используйте формат ДД.ММ.ГГГГ")
            return
        
        print(f"\nВведите показания на {reading_date.strftime('%d.%m.%Y')}:")
        
        for counter in counters:
            # Получаем последнее показание
            latest_reading = self.reading_service.get_latest_reading_by_counter(counter.id)
            last_value = latest_reading.value if latest_reading else 0
            
            print(f"\n{counter.description} ({counter.number})")
            print(f"Последнее показание: {last_value} м³")
            
            while True:
                try:
                    value = int(input("Новое показание (м³): "))
                    if value < last_value:
                        print(f"❌ Новое показание не может быть меньше предыдущего ({last_value})")
                        continue
                    
                    # Создаем показание
                    reading_data = ReadingCreate(
                        counter_id=counter.id,
                        value=value,
                        reading_date=reading_date
                    )
                    
                    self.reading_service.create_reading(reading_data)
                    print(f"✅ Показание {value} м³ сохранено")
                    break
                    
                except ValueError:
                    print("❌ Введите целое число")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
    
    def show_counters(self):
        """Просмотр счетчиков"""
        print("\n🔧 СЧЕТЧИКИ")
        print("-"*30)
        
        counters = self.counter_service.get_all_counters()
        if not counters:
            print("Счетчики не найдены")
            return
        
        for counter in counters:
            latest_reading = self.reading_service.get_latest_reading_by_counter(counter.id)
            last_value = latest_reading.value if latest_reading else "Нет данных"
            last_date = latest_reading.reading_date.strftime("%d.%m.%Y") if latest_reading else "Нет данных"
            
            print(f"\n{counter.description}")
            print(f"  Номер: {counter.number}")
            print(f"  Тип: {'Горячая вода' if counter.water_type == 'hot' else 'Холодная вода'}")
            print(f"  Последнее показание: {last_value} м³ ({last_date})")
    
    def show_readings_history(self):
        """Просмотр истории показаний"""
        print("\n📈 ИСТОРИЯ ПОКАЗАНИЙ")
        print("-"*30)
        
        counters = self.counter_service.get_all_counters()
        if not counters:
            print("Счетчики не найдены")
            return
        
        for counter in counters:
            print(f"\n{counter.description} ({counter.number})")
            print("-" * 40)
            
            readings = self.reading_service.get_readings_by_counter(counter.id, 5)
            if not readings:
                print("  Нет данных")
                continue
            
            for reading in readings:
                print(f"  {reading.reading_date.strftime('%d.%m.%Y')}: {reading.value} м³")
    
    def calculate_monthly_payment(self):
        """Расчет платежа за месяц"""
        print("\n💰 РАСЧЕТ ПЛАТЕЖА ЗА МЕСЯЦ")
        print("-"*30)
        
        # Получаем текущий год и месяц по умолчанию
        current_date = datetime.now()
        default_year = current_date.year
        default_month = current_date.month
        
        try:
            year_input = input(f"Введите год (по умолчанию {default_year}): ").strip()
            year = int(year_input) if year_input else default_year
            
            month_input = input(f"Введите месяц (1-12, по умолчанию {default_month}): ").strip()
            month = int(month_input) if month_input else default_month
            
            if month < 1 or month > 12:
                print("❌ Месяц должен быть от 1 до 12")
                return
            
            calculation = self.payment_service.calculate_monthly_payment(year, month)
            
            print(f"\n📊 РАСЧЕТ ЗА {month:02d}.{year}")
            print("="*40)
            print(f"Период: {calculation.period_start.strftime('%d.%m.%Y')} - {calculation.period_end.strftime('%d.%m.%Y')}")
            print(f"Потребление холодной воды: {calculation.cold_water_consumption} м³")
            print(f"Потребление горячей воды: {calculation.hot_water_consumption} м³")
            print(f"Утилизация воды: {calculation.wastewater_consumption} м³")
            print(f"Тариф холодной воды: {calculation.cold_water_rate:.2f} руб/м³")
            print(f"Тариф горячей воды: {calculation.hot_water_rate:.2f} руб/м³")
            print(f"Тариф утилизации: {calculation.wastewater_rate:.2f} руб/м³")
            print(f"Сумма за холодную воду: {calculation.cold_water_consumption * calculation.cold_water_rate:.2f} руб")
            print(f"Сумма за горячую воду: {calculation.hot_water_consumption * calculation.hot_water_rate:.2f} руб")
            print(f"Сумма за утилизацию: {calculation.wastewater_consumption * calculation.wastewater_rate:.2f} руб")
            print(f"ИТОГО: {calculation.total_amount:.2f} руб")
            
            save = input("\nСохранить расчет в истории? (y/n): ").lower()
            if save == 'y':
                notes = input("Примечания (необязательно): ").strip() or None
                payment = self.payment_service.create_payment(calculation, notes)
                print(f"✅ Платеж сохранен с ID: {payment.id}")
                
        except ValueError as e:
            print(f"❌ Ошибка расчета: {e}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def show_payments_history(self):
        """Просмотр истории платежей"""
        print("\n💳 ИСТОРИЯ ПЛАТЕЖЕЙ")
        print("-"*30)
        
        payments = self.payment_service.get_all_payments()
        if not payments:
            print("Платежи не найдены")
            return
        
        for payment in payments:
            print(f"\nПлатеж #{payment.id}")
            print(f"Период: {payment.period_start.strftime('%d.%m.%Y')} - {payment.period_end.strftime('%d.%m.%Y')}")
            print(f"Холодная вода: {payment.cold_water_consumption} м³ = {payment.cold_water_amount:.2f} руб")
            print(f"Горячая вода: {payment.hot_water_consumption} м³ = {payment.hot_water_amount:.2f} руб")
            print(f"Утилизация: {payment.wastewater_consumption} м³ = {payment.wastewater_amount:.2f} руб")
            print(f"ИТОГО: {payment.total_amount:.2f} руб")
            if payment.notes:
                print(f"Примечания: {payment.notes}")
            print(f"Рассчитан: {payment.calculated_at.strftime('%d.%m.%Y %H:%M')}")
    
    def manage_tariffs(self):
        """Управление тарифами"""
        print("\n⚙️ УПРАВЛЕНИЕ ТАРИФАМИ")
        print("-"*30)
        
        while True:
            print("\n1. Просмотреть текущие тарифы")
            print("2. Изменить тариф")
            print("0. Назад")
            
            choice = input("\nВыберите действие: ").strip()
            
            if choice == "1":
                self.show_current_tariffs()
            elif choice == "2":
                self.change_tariff()
            elif choice == "0":
                break
            else:
                print("❌ Неверный выбор")
    
    def show_current_tariffs(self):
        """Показать текущие тарифы"""
        print("\n📋 ТЕКУЩИЕ ТАРИФЫ")
        print("-"*30)
        
        hot_tariff = self.payment_service.get_current_tariff("hot_water")
        cold_tariff = self.payment_service.get_current_tariff("cold_water")
        wastewater_tariff = self.payment_service.get_current_tariff("wastewater")
        
        if cold_tariff:
            print(f"Холодная вода: {cold_tariff.price_per_cubic_meter:.2f} руб/м³")
            print(f"Действует с: {cold_tariff.start_date.strftime('%d.%m.%Y')}")
        else:
            print("❌ Тариф на холодную воду не установлен")
        
        if hot_tariff:
            print(f"Горячая вода: {hot_tariff.price_per_cubic_meter:.2f} руб/м³")
            print(f"Действует с: {hot_tariff.start_date.strftime('%d.%m.%Y')}")
        else:
            print("❌ Тариф на горячую воду не установлен")
        
        if wastewater_tariff:
            print(f"Утилизация: {wastewater_tariff.price_per_cubic_meter:.2f} руб/м³")
            print(f"Действует с: {wastewater_tariff.start_date.strftime('%d.%m.%Y')}")
        else:
            print("❌ Тариф на утилизацию не установлен")
    
    def change_tariff(self):
        """Изменить тариф"""
        print("\n💰 ИЗМЕНЕНИЕ ТАРИФА")
        print("-"*30)
        
        print("Доступные типы услуг:")
        print("1. cold_water - холодная вода")
        print("2. hot_water - горячая вода (подогрев)")
        print("3. wastewater - утилизация")
        
        service_type = input("Введите тип услуги: ").strip().lower()
        if service_type not in ["cold_water", "hot_water", "wastewater"]:
            print("❌ Неверный тип услуги. Используйте 'cold_water', 'hot_water' или 'wastewater'")
            return
        
        try:
            price = float(input("Новая цена за м³ (руб): "))
            if price <= 0:
                print("❌ Цена должна быть больше 0")
                return
            
            # Создаем новый тариф
            self.payment_service.create_tariff(service_type, price, datetime.now())
            
            service_names = {
                "cold_water": "холодную воду",
                "hot_water": "горячую воду (подогрев)",
                "wastewater": "утилизацию"
            }
            print(f"✅ Тариф на {service_names.get(service_type, service_type)} изменен на {price:.2f} руб/м³")
            
        except ValueError:
            print("❌ Неверный формат цены")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def initialize_system(self):
        """Инициализация системы"""
        print("\n🚀 ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ")
        print("-"*30)
        
        print("Создание счетчиков по умолчанию...")
        counters = self.counter_service.initialize_default_counters()
        print(f"✅ Создано {len(counters)} счетчиков")
        
        print("Создание тарифов по умолчанию...")
        tariffs = self.payment_service.initialize_default_tariffs()
        print(f"✅ Создано {len(tariffs)} тарифов")
        
        print("\n🎉 Система инициализирована!")
    
    def manage_counters(self):
        """Управление счетчиками"""
        print("\n🔧 УПРАВЛЕНИЕ СЧЕТЧИКАМИ")
        print("-"*30)
        
        while True:
            print("\n1. Просмотреть все счетчики")
            print("2. Добавить новый счетчик")
            print("3. Редактировать счетчик")
            print("4. Удалить счетчик")
            print("0. Назад")
            
            choice = input("\nВыберите действие: ").strip()
            
            if choice == "1":
                self.show_counters()
            elif choice == "2":
                self.add_counter()
            elif choice == "3":
                self.edit_counter()
            elif choice == "4":
                self.delete_counter()
            elif choice == "0":
                break
            else:
                print("❌ Неверный выбор")
    
    def add_counter(self):
        """Добавление нового счетчика"""
        print("\n➕ ДОБАВЛЕНИЕ СЧЕТЧИКА")
        print("-"*30)
        
        try:
            number = input("Номер счетчика: ").strip()
            if not number:
                print("❌ Номер счетчика не может быть пустым")
                return
            
            # Проверяем, не существует ли уже счетчик с таким номером
            existing = self.counter_service.get_counter_by_number(number)
            if existing:
                print(f"❌ Счетчик с номером '{number}' уже существует")
                return
            
            print("Тип воды:")
            print("1. hot - горячая вода")
            print("2. cold - холодная вода")
            
            water_type = input("Выберите тип (1 или 2): ").strip()
            if water_type == "1":
                water_type = "hot"
            elif water_type == "2":
                water_type = "cold"
            else:
                print("❌ Неверный выбор типа воды")
                return
            
            description = input("Описание (необязательно): ").strip() or None
            
            # Создаем счетчик
            counter_data = CounterCreate(
                number=number,
                water_type=water_type,
                description=description
            )
            
            new_counter = self.counter_service.create_counter(counter_data)
            print(f"✅ Счетчик '{number}' успешно создан с ID: {new_counter.id}")
            
        except Exception as e:
            print(f"❌ Ошибка при создании счетчика: {e}")
    
    def edit_counter(self):
        """Редактирование счетчика"""
        print("\n✏️ РЕДАКТИРОВАНИЕ СЧЕТЧИКА")
        print("-"*30)
        
        # Показываем список счетчиков
        counters = self.counter_service.get_all_counters()
        if not counters:
            print("❌ Счетчики не найдены")
            return
        
        print("Доступные счетчики:")
        for i, counter in enumerate(counters, 1):
            print(f"{i}. {counter.number} - {counter.description or 'Без описания'}")
        
        try:
            choice = int(input("\nВыберите номер счетчика для редактирования: "))
            if choice < 1 or choice > len(counters):
                print("❌ Неверный номер")
                return
            
            counter = counters[choice - 1]
            print(f"\nРедактирование счетчика: {counter.number}")
            print(f"Текущее описание: {counter.description or 'Без описания'}")
            print(f"Текущий тип: {'Горячая вода' if counter.water_type == 'hot' else 'Холодная вода'}")
            
            while True:
                print("\nЧто хотите отредактировать?")
                print("1. Номер счетчика")
                print("2. Тип счетчика")
                print("3. Название/описание")
                print("0. Завершить редактирование")
                
                edit_choice = input("Выберите действие: ").strip()
                
                if edit_choice == "1":
                    self.edit_counter_number(counter)
                elif edit_choice == "2":
                    self.edit_counter_type(counter)
                elif edit_choice == "3":
                    self.edit_counter_description(counter)
                elif edit_choice == "0":
                    break
                else:
                    print("❌ Неверный выбор")
                
                # Обновляем данные счетчика после каждого изменения
                counter = self.counter_service.get_counter(counter.id)
                if not counter:
                    print("❌ Счетчик не найден")
                    return
                
                print(f"\nТекущие данные счетчика:")
                print(f"Номер: {counter.number}")
                print(f"Тип: {'Горячая вода' if counter.water_type == 'hot' else 'Холодная вода'}")
                print(f"Описание: {counter.description or 'Без описания'}")
                
        except ValueError:
            print("❌ Введите корректный номер")
        except Exception as e:
            print(f"❌ Ошибка при редактировании: {e}")
    
    def edit_counter_number(self, counter):
        """Редактирование номера счетчика"""
        print(f"\n📝 РЕДАКТИРОВАНИЕ НОМЕРА СЧЕТЧИКА")
        print("-"*40)
        print(f"Текущий номер: {counter.number}")
        
        new_number = input("Новый номер (Enter для отмены): ").strip()
        if not new_number:
            print("❌ Редактирование отменено")
            return
        
        # Проверяем, не занят ли новый номер другим счетчиком
        if new_number != counter.number:
            existing = self.counter_service.get_counter_by_number(new_number)
            if existing:
                print(f"❌ Счетчик с номером '{new_number}' уже существует")
                return
        
        # Обновляем счетчик
        counter_data = CounterCreate(
            number=new_number,
            water_type=counter.water_type,
            description=counter.description
        )
        
        updated_counter = self.counter_service.update_counter(counter.id, counter_data)
        if updated_counter:
            print(f"✅ Номер счетчика изменен на '{new_number}'")
        else:
            print("❌ Ошибка при обновлении номера")
    
    def edit_counter_type(self, counter):
        """Редактирование типа счетчика"""
        print(f"\n🌊 РЕДАКТИРОВАНИЕ ТИПА СЧЕТЧИКА")
        print("-"*40)
        print(f"Текущий тип: {'Горячая вода' if counter.water_type == 'hot' else 'Холодная вода'}")
        
        print("Выберите новый тип:")
        print("1. hot - горячая вода")
        print("2. cold - холодная вода")
        print("0. Отмена")
        
        type_choice = input("Ваш выбор: ").strip()
        
        if type_choice == "0":
            print("❌ Редактирование отменено")
            return
        elif type_choice == "1":
            new_water_type = "hot"
        elif type_choice == "2":
            new_water_type = "cold"
        else:
            print("❌ Неверный выбор")
            return
        
        # Обновляем счетчик
        counter_data = CounterCreate(
            number=counter.number,
            water_type=new_water_type,
            description=counter.description
        )
        
        updated_counter = self.counter_service.update_counter(counter.id, counter_data)
        if updated_counter:
            print(f"✅ Тип счетчика изменен на '{'Горячая вода' if new_water_type == 'hot' else 'Холодная вода'}'")
        else:
            print("❌ Ошибка при обновлении типа")
    
    def edit_counter_description(self, counter):
        """Редактирование описания счетчика"""
        print(f"\n📄 РЕДАКТИРОВАНИЕ ОПИСАНИЯ СЧЕТЧИКА")
        print("-"*40)
        print(f"Текущее описание: {counter.description or 'Без описания'}")
        
        new_description = input("Новое описание (Enter для отмены): ").strip()
        if not new_description:
            print("❌ Редактирование отменено")
            return
        
        # Обновляем счетчик
        counter_data = CounterCreate(
            number=counter.number,
            water_type=counter.water_type,
            description=new_description
        )
        
        updated_counter = self.counter_service.update_counter(counter.id, counter_data)
        if updated_counter:
            print(f"✅ Описание счетчика изменено на '{new_description}'")
        else:
            print("❌ Ошибка при обновлении описания")
    
    def delete_counter(self):
        """Удаление счетчика"""
        print("\n🗑️ УДАЛЕНИЕ СЧЕТЧИКА")
        print("-"*30)
        
        # Показываем список счетчиков
        counters = self.counter_service.get_all_counters()
        if not counters:
            print("❌ Счетчики не найдены")
            return
        
        print("Доступные счетчики:")
        for i, counter in enumerate(counters, 1):
            print(f"{i}. {counter.number} - {counter.description or 'Без описания'}")
        
        try:
            choice = int(input("\nВыберите номер счетчика для удаления: "))
            if choice < 1 or choice > len(counters):
                print("❌ Неверный номер")
                return
            
            counter = counters[choice - 1]
            
            # Проверяем, есть ли показания у этого счетчика
            readings = self.reading_service.get_readings_by_counter(counter.id)
            if readings:
                print(f"⚠️ Внимание! У счетчика '{counter.number}' есть {len(readings)} показаний.")
                confirm = input("Удаление счетчика также удалит все его показания. Продолжить? (y/n): ").lower()
                if confirm != 'y':
                    print("❌ Удаление отменено")
                    return
            
            # Удаляем счетчик
            if self.counter_service.delete_counter(counter.id):
                print(f"✅ Счетчик '{counter.number}' успешно удален")
            else:
                print("❌ Ошибка при удалении счетчика")
                
        except ValueError:
            print("❌ Введите корректный номер")
        except Exception as e:
            print(f"❌ Ошибка при удалении: {e}")
    
    def run(self):
        """Запуск приложения"""
        print("🌊 Добро пожаловать в Water Counter!")
        
        while True:
            self.show_main_menu()
            choice = input("Выберите действие: ").strip()
            
            if choice == "1":
                self.input_readings()
            elif choice == "2":
                self.show_counters()
            elif choice == "3":
                self.show_readings_history()
            elif choice == "4":
                self.calculate_monthly_payment()
            elif choice == "5":
                self.show_payments_history()
            elif choice == "6":
                self.manage_tariffs()
            elif choice == "7":
                self.manage_counters()
            elif choice == "8":
                self.initialize_system()
            elif choice == "0":
                print("👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор. Попробуйте снова.")
            
            input("\nНажмите Enter для продолжения...")
