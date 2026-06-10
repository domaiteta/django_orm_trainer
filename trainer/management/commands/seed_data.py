"""
Наполнение БД данными для тренажёра. Запуск: python manage.py seed_data
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from trainer.models import (
    Author,
    BleGroup,
    BleGroupRouteDate,
    BleInspectionRecord,
    BleRoute,
    BleTag,
    Book,
    Category,
    Company,
    ConstructionSite,
    InspectionGap,
    OrgObject,
    Profile,
    Publisher,
    Review,
    Shelf,
    TimesheetPlan,
)


def date(y, m, d):
    return timezone.now().date().replace(year=y, month=m, day=d)


class Command(BaseCommand):
    help = 'Создаёт издательства, авторов, книги, категории и отзывы для тренажёра'

    def handle(self, *args, **options):
        # Сбрасываем всё для повторяемых тренировок
        BleInspectionRecord.objects.all().delete()
        BleGroupRouteDate.objects.all().delete()
        BleTag.objects.all().delete()
        BleGroup.objects.all().delete()
        BleRoute.objects.all().delete()
        TimesheetPlan.objects.all().delete()
        OrgObject.objects.all().delete()
        ConstructionSite.objects.all().delete()
        InspectionGap.objects.all().delete()
        Company.objects.all().delete()

        Publisher.objects.all().delete()
        Author.objects.all().delete()
        Category.objects.all().delete()
        Shelf.objects.all().delete()
        Book.objects.all().delete()

        publishers = [
            Publisher(name='Питер', founded_year=1991, country='Россия', is_active=True),
            Publisher(name='Эксмо', founded_year=1991, country='Россия', is_active=True),
            Publisher(name='O\'Reilly', founded_year=1978, country='США', is_active=True),
            Publisher(name='Manning', founded_year=1993, country='США', is_active=True),
            Publisher(name='Старая типография', founded_year=1950, country='Россия', is_active=False),
        ]
        Publisher.objects.bulk_create(publishers)
        p_piter, p_eksmo, p_oreilly, p_manning, p_old = Publisher.objects.order_by('pk')

        authors = [
            Author(name='Иван Петров', birth_year=1980, country='Россия'),
            Author(name='Мария Сидорова', birth_year=1985, country='Россия'),
            Author(name='John Smith', birth_year=1975, country='США'),
            Author(name='Анна Козлова', birth_year=1990, country='Россия'),
            Author(name='Без книг', birth_year=2000, country='Россия'),
        ]
        Author.objects.bulk_create(authors)
        a_ivan, a_maria, a_john, a_anna, a_empty = Author.objects.order_by('pk')

        Profile.objects.bulk_create([
            Profile(author=a_ivan, bio='Писатель-программист', website='https://ivan.example', verified=True),
            Profile(author=a_maria, bio='Технический писатель', website='', verified=True),
            Profile(author=a_john, bio='Author from USA', website='https://john.example', verified=False),
            Profile(author=a_anna, bio='', website='', verified=False),
        ])

        categories = [
            Category(name='Программирование', slug='programming'),
            Category(name='Базы данных', slug='databases'),
            Category(name='Веб-разработка', slug='web'),
            Category(name='Python', slug='python'),
            Category(name='Django', slug='django'),
        ]
        Category.objects.bulk_create(categories)
        cat_prog, cat_db, cat_web, cat_py, cat_django = Category.objects.order_by('pk')

        books = [
            Book(title='Django за 21 день', author=a_ivan, publisher=p_piter, price=Decimal('899.00'),
                 published_at=date(2022, 5, 10), is_published=True, pages=350),
            Book(title='Python для всех', author=a_maria, publisher=p_eksmo, price=Decimal('650.00'),
                 published_at=date(2021, 3, 1), is_published=True, pages=400),
            Book(title='ORM и SQL', author=a_ivan, publisher=p_piter, price=Decimal('1200.00'),
                 published_at=date(2023, 1, 15), is_published=True, pages=280),
            Book(title='Веб-фреймворки', author=a_john, publisher=p_oreilly, price=Decimal('1500.00'),
                 published_at=date(2020, 11, 20), is_published=True, pages=500),
            Book(title='Черновик книги', author=a_anna, publisher=p_manning, price=None,
                 published_at=None, is_published=False, pages=100),
            Book(title='Ещё один черновик', author=a_anna, publisher=None, price=Decimal('100.00'),
                 published_at=date(2024, 1, 1), is_published=False, pages=50),
            Book(title='Книга без автора', author=None, publisher=p_old, price=Decimal('200.00'),
                 published_at=date(2010, 5, 5), is_published=True, pages=200),
            Book(title='Дорогая книга', author=a_john, publisher=p_oreilly, price=Decimal('5000.00'),
                 published_at=date(2022, 6, 1), is_published=True, pages=600),
        ]
        Book.objects.bulk_create(books)
        b_django, b_python, b_orm, b_web, b_draft1, b_draft2, b_no_author, b_expensive = Book.objects.order_by('pk')

        b_django.categories.add(cat_django, cat_py, cat_web)
        b_python.categories.add(cat_py, cat_prog)
        b_orm.categories.add(cat_db, cat_prog)
        b_web.categories.add(cat_web, cat_prog)
        b_expensive.categories.add(cat_prog)

        reviews = [
            Review(book=b_django, author_name='Читатель', rating=5, text='Отлично!'),
            Review(book=b_django, author_name='Новичок', rating=4, text='Понятно объяснено'),
            Review(book=b_python, author_name='Студент', rating=5, text=''),
            Review(book=b_orm, author_name='Девопс', rating=3, text='Сложновато'),
            Review(book=b_web, author_name='John', rating=4, text='Good'),
            Review(book=b_expensive, author_name='Критик', rating=1, text='Дорого'),
        ]
        Review.objects.bulk_create(reviews)

        Shelf.objects.bulk_create([
            Shelf(label='Витрина-A', book=b_django),
            Shelf(label='Витрина-A', book=b_python),
            Shelf(label='Склад-B', book=b_orm),
            Shelf(label='Резерв', book=b_django),
        ])

        # BLE-домен
        now = timezone.now()
        today = now.date()

        company = Company.objects.create(name='Acme Build')
        cs_north = ConstructionSite.objects.create(company=company, title='Площадка Север')
        cs_south = ConstructionSite.objects.create(company=company, title='Площадка Юг')
        cs_old = ConstructionSite.objects.create(company=company, title='Площадка Архив', deleted=now)

        obj_north_1 = OrgObject.objects.create(
            company=company,
            construction_site=cs_north,
            title='Объект Север-1',
            utc_offset_hours=3,
        )
        obj_north_2 = OrgObject.objects.create(
            company=company,
            construction_site=cs_north,
            title='Объект Север-2',
            utc_offset_hours=4,
        )
        obj_south = OrgObject.objects.create(
            company=company,
            construction_site=cs_south,
            title='Объект Юг-1',
            utc_offset_hours=5,
        )
        obj_default = OrgObject.objects.create(
            company=company,
            construction_site=None,
            title='Объект По Умолчанию',
            utc_offset_hours=2,
        )

        TimesheetPlan.objects.bulk_create([
            TimesheetPlan(org_object=obj_north_2, title='План Север'),
            TimesheetPlan(org_object=obj_south, title='План Юг'),
        ])

        InspectionGap.objects.create(days=2)

        route_a = BleRoute.objects.create(company=company, title='Маршрут А')
        route_b = BleRoute.objects.create(company=company, title='Маршрут B')
        route_c = BleRoute.objects.create(company=company, title='Маршрут C')

        group_10 = BleGroup.objects.create(company=company, title='Группа 10', group_number=10)
        group_20 = BleGroup.objects.create(company=company, title='Группа 20', group_number=20)

        BleGroupRouteDate.objects.bulk_create([
            BleGroupRouteDate(ble_group=group_10, ble_route=route_a, dt=today),
            BleGroupRouteDate(ble_group=group_20, ble_route=route_b, dt=today),
            BleGroupRouteDate(ble_group=group_10, ble_route=route_a, dt=today - timedelta(days=1)),
        ])

        ble_1 = BleTag.objects.create(
            company=company,
            construction_site=cs_north,
            ble_route=route_a,
            ble_number='BLE-001',
            mac_address='AA:AA:AA:AA:AA:01',
            chip_uuid='chip-001',
            status=BleTag.Status.INSTALLED_WORKING,
            bypass_status=1,
            charge_value=80,
            latitude=55.11,
            longitude=37.11,
            hardware_version='1.0',
            power=10,
            frequency=2,
        )
        ble_2 = BleTag.objects.create(
            company=company,
            construction_site=cs_north,
            ble_route=route_b,
            ble_number='BLE-002',
            mac_address='AA:AA:AA:AA:AA:02',
            chip_uuid='chip-002',
            status=BleTag.Status.INSTALLED_WORKING,
            bypass_status=1,
            charge_value=12,
            latitude=55.12,
            longitude=37.12,
            hardware_version='1.1',
            power=12,
            frequency=3,
        )
        ble_3 = BleTag.objects.create(
            company=company,
            construction_site=cs_south,
            ble_route=route_c,
            ble_number='BLE-003',
            mac_address='AA:AA:AA:AA:AA:03',
            chip_uuid='chip-003',
            status=BleTag.Status.INSTALLED_NOT_WORKING,
            bypass_status=0,
            charge_value=50,
            latitude=55.13,
            longitude=37.13,
            hardware_version='1.0',
            power=8,
            frequency=2,
        )
        ble_4 = BleTag.objects.create(
            company=company,
            construction_site=None,
            ble_route=None,
            ble_number='BLE-004',
            mac_address='AA:AA:AA:AA:AA:04',
            chip_uuid='chip-004',
            status=BleTag.Status.INSTALLED_WORKING,
            bypass_status=0,
            charge_value=14,
        )
        ble_5 = BleTag.objects.create(
            company=company,
            construction_site=cs_south,
            ble_route=route_a,
            ble_number='BLE-005',
            mac_address='AA:AA:AA:AA:AA:05',
            chip_uuid='chip-005',
            status=BleTag.Status.IN_STOCK,
            bypass_status=0,
            charge_value=99,
        )

        BleInspectionRecord.objects.bulk_create([
            BleInspectionRecord(ble=ble_1, record_dt=now - timedelta(hours=5)),
            BleInspectionRecord(ble=ble_1, record_dt=now - timedelta(days=3)),
            BleInspectionRecord(ble=ble_2, record_dt=now - timedelta(days=1)),
            BleInspectionRecord(ble=ble_4, record_dt=now - timedelta(days=1)),
            BleInspectionRecord(ble=ble_5, record_dt=now - timedelta(days=10)),
        ])

        self.stdout.write(
            self.style.SUCCESS(
                'Данные созданы: книги + BLE-домен (company, объекты, площадки, маршруты, группы, планы, метки, обходы).'
            )
        )
