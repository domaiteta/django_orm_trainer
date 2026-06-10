"""
Модели для тренажёра: от базового ORM до сложных боевых запросов.
"""
from django.db import models


class Publisher(models.Model):
    """Издательство. Связь: Book — ForeignKey сюда."""
    name = models.CharField('Название', max_length=200)
    founded_year = models.PositiveIntegerField('Год основания', null=True, blank=True)
    country = models.CharField('Страна', max_length=100, blank=True)
    is_active = models.BooleanField('Активно', default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Издательство'
        verbose_name_plural = 'Издательства'

    def __str__(self):
        return self.name


class Author(models.Model):
    """Автор. Связи: OneToOne с Profile, Book — ForeignKey сюда."""
    name = models.CharField('Имя', max_length=200)
    birth_year = models.PositiveIntegerField('Год рождения', null=True, blank=True)
    country = models.CharField('Страна', max_length=100, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'

    def __str__(self):
        return self.name


class Profile(models.Model):
    """Профиль автора. OneToOne с Author — для отработки select_related / one-to-one."""
    author = models.OneToOneField(
        Author,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
    )
    bio = models.TextField('Биография', blank=True)
    website = models.URLField('Сайт', blank=True)
    verified = models.BooleanField('Верифицирован', default=False)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль: {self.author.name}'


class Category(models.Model):
    """Категория книг. ManyToMany с Book."""
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Book(models.Model):
    """Книга. ForeignKey к Publisher и Author, ManyToMany с Category."""
    title = models.CharField('Название', max_length=300)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='books',
        null=True,
        blank=True,
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        related_name='books',
        null=True,
        blank=True,
    )
    categories = models.ManyToManyField(
        Category,
        related_name='books',
        blank=True,
    )
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, null=True, blank=True)
    published_at = models.DateField('Дата публикации', null=True, blank=True)
    is_published = models.BooleanField('Опубликована', default=True)
    pages = models.PositiveIntegerField('Страниц', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'

    def __str__(self):
        return self.title


class Review(models.Model):
    """Отзыв на книгу. ForeignKey к Book — для цепочек и prefetch."""
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    author_name = models.CharField('Имя автора отзыва', max_length=200)
    rating = models.PositiveSmallIntegerField('Рейтинг (1-5)', null=True, blank=True)
    text = models.TextField('Текст', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.author_name} — {self.book.title}'


class Shelf(models.Model):
    """
    Полка в каталоге: FK на Book без related_name.
    Обратный доступ с книги: book.shelf_set (менеджер по умолчанию Django).
    """
    label = models.CharField('Метка полки', max_length=100)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Полка'
        verbose_name_plural = 'Полки'

    def __str__(self):
        return f'{self.label} → {self.book_id}'


# --- BLE-домен для продвинутых ORM-задач ---

class Company(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ConstructionSite(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='construction_sites')
    title = models.CharField(max_length=255)
    deleted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class OrgObject(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='org_objects')
    construction_site = models.ForeignKey(
        ConstructionSite,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='org_objects',
    )
    title = models.CharField(max_length=255)
    utc_offset_hours = models.IntegerField(default=0)
    deleted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class BleRoute(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ble_routes')
    title = models.CharField(max_length=255)
    deleted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class BleGroup(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ble_groups')
    title = models.CharField(max_length=255)
    group_number = models.IntegerField()
    deleted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class BleGroupRouteDate(models.Model):
    ble_group = models.ForeignKey(BleGroup, on_delete=models.CASCADE, related_name='route_dates')
    ble_route = models.ForeignKey(BleRoute, on_delete=models.CASCADE, related_name='group_dates')
    dt = models.DateField()

    class Meta:
        ordering = ['-id']


class TimesheetPlan(models.Model):
    org_object = models.ForeignKey(OrgObject, on_delete=models.CASCADE, related_name='timesheet_plans')
    title = models.CharField(max_length=255, blank=True)
    dt = models.DateField(null=True, blank=True)


class InspectionGap(models.Model):
    days = models.PositiveIntegerField(default=2)
    updated_at = models.DateTimeField(auto_now=True)


class BleTag(models.Model):
    class Status(models.IntegerChoices):
        INSTALLED_WORKING = 1, 'Установлена, работает'
        INSTALLED_NOT_WORKING = 2, 'Установлена, не работает'
        IN_STOCK = 3, 'На складе'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ble_tags')
    construction_site = models.ForeignKey(
        ConstructionSite,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ble_tags',
    )
    ble_route = models.ForeignKey(
        BleRoute,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ble_tags',
    )
    ble_number = models.CharField(max_length=100)
    mac_address = models.CharField(max_length=100)
    chip_uuid = models.CharField(max_length=100, blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.IN_STOCK)
    bypass_status = models.IntegerField(default=0)
    charge_value = models.IntegerField(default=100)
    movability_type = models.IntegerField(default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    ble_type = models.IntegerField(default=0)
    ble_zone_id = models.IntegerField(null=True, blank=True)
    hardware_version = models.CharField(max_length=50, blank=True)
    power = models.IntegerField(default=0)
    frequency = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.ble_number


class BleInspectionRecord(models.Model):
    ble = models.ForeignKey(BleTag, on_delete=models.CASCADE, related_name='inspection_records')
    record_dt = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-record_dt']


# --- Темы и задания тренажёра ---

class Topic(models.Model):
    """Раздел тренажёра (фильтрация, связи, lookups и т.д.)."""
    slug = models.SlugField(unique=True)
    name = models.CharField('Название', max_length=200)
    order = models.PositiveIntegerField('Порядок', default=0)
    theory = models.TextField('Теория (кратко)', blank=True)

    class Meta:
        ordering = ['order', 'pk']

    def __str__(self):
        return self.name


class Task(models.Model):
    """Задание: теория (опционально), формулировка, эталонный код."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tasks')
    order = models.PositiveIntegerField('Порядок', default=0)
    theory = models.TextField('Теория перед заданием', blank=True)
    problem = models.TextField('Формулировка задания')
    solution_code = models.TextField('Эталонный код (возвращает QuerySet)')
    hint_model = models.CharField(
        'Подсказка: основная модель',
        max_length=50,
        blank=True,
        help_text='Например: Book',
    )

    class Meta:
        ordering = ['topic', 'order']

    def __str__(self):
        return f'{self.topic.name} — {self.problem[:50]}...'
