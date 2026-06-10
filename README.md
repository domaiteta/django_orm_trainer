# Тренажёр Django ORM

Тренажёр для отработки Django ORM с авто-проверкой: от базы до production-паттернов (`Subquery`, `OuterRef`, `Exists`, `Case/When`) на большом BLE-сценарии.

## Запуск

```bash
# Установка зависимостей
pip install Django django-cors-headers

# Миграции
python manage.py migrate

# Наполнение БД (издательства, авторы, книги, категории, отзывы)
python manage.py seed_data

# Загрузка тем и заданий (расширенный банк задач)
python manage.py load_tasks

# Сервер
python manage.py runserver
```

Откройте в браузере: http://127.0.0.1:8000/

## Структура

- **Базовый домен**: `Publisher`, `Author`, `Profile`, `Category`, `Book`, `Review`.
- **Продвинутый BLE-домен**: `Company`, `ConstructionSite`, `OrgObject`, `TimesheetPlan`, `InspectionGap`, `BleRoute`, `BleGroup`, `BleGroupRouteDate`, `BleTag`, `BleInspectionRecord`.
- **Темы и задания** (`trainer/data/tasks_data.py`): расширенный трек до уровня сложных запросов с десятками задач по каждому блоку, включая практику шагов из real-world BLE-запроса.
- **Проверка** (`trainer/checker.py`): ограниченное, но широкое окружение (ORM-модели + `Q/F`, агрегаты, `Subquery/OuterRef/Exists`, `Case/When`, `Value`, типы полей, `Coalesce`, `timezone`, `timedelta`).

## Как решать задачи

В поле ввода вводите **одно выражение**, возвращающее QuerySet, например:

- `Book.objects.all()`
- `Book.objects.filter(is_published=True)`
- `Book.objects.filter(author__country="Россия")`
- `Book.objects.filter(Q(price__gt=500) | Q(pages__lt=200))`
- `BleTag.objects.annotate(group_id=Subquery(...OuterRef(...))).filter(...)`

Не присваивайте результат в переменную — только выражение QuerySet.
