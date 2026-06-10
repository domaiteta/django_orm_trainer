# -*- coding: utf-8 -*-
"""
Большой учебный банк задач для Django ORM.
Цель: от нуля до уверенного написания сложных запросов уровня production.
"""


# Подсказка к задачам, где фигурирует «сегодня» (согласовано с checker и USE_TZ)
SUBQUERY_SINGLE_COL_NOTE = (
    '<p><b>Subquery:</b> внутренний QuerySet должен выбирать <b>ровно одну колонку</b> — через '
    '<code>.values("record_dt")[:1]</code> (или цепочку <code>values → annotate → values</code>). '
    'Передавать в <code>Subquery(...)</code> «полную» выборку модели без <code>values(...)</code> нельзя: '
    'у выражения не будет <code>output_field</code>, и запрос не соберётся.</p>'
    '<p><b>«Последний обход» по времени:</b> нужна строка с максимальным <code>record_dt</code>. '
    'Сортировка <code>order_by("-id")</code> выбирает запись с <b>наибольшим первичным ключом</b> — это '
    'не то же самое, что «самая свежая дата обхода» (порядок <code>bulk_create</code> и время могут разъехаться). '
    'Используй <code>order_by("-record_dt")</code> + <code>values("record_dt")[:1]</code> или '
    '<code>values("ble_id").annotate(m=Max("record_dt")).values("m")[:1]</code>.</p>'
)

TZ_TASK_NOTE = (
    '<p><b>Сегодня:</b> используй <code>timezone.now().date()</code>. '
    'Имя <code>timezone</code> — это модуль <code>django.utils.timezone</code> '
    '(<a href="https://docs.djangoproject.com/en/stable/topics/i18n/timezones/" target="_blank">документация</a>); '
    'в тренажёре он уже доступен в коде проверки, отдельный <code>import</code> не нужен. '
    'Лучше не использовать <code>datetime.now().date()</code>: при <code>USE_TZ = True</code> «сегодня» может не совпасть с эталоном.</p>'
)


def _tasks(rows, default_hint):
    out = []
    for i, row in enumerate(rows, start=1):
        problem, solution, *rest = row
        theory = rest[0] if rest else ''
        hint_model = rest[1] if len(rest) > 1 else default_hint
        out.append({
            'order': i,
            'theory': theory,
            'problem': problem,
            'solution_code': solution,
            'hint_model': hint_model,
        })
    return out


TOPICS = [
    {
        'slug': 'orm-base',
        'name': 'База ORM: QuerySet, filter, exclude',
        'order': 1,
        'theory': """
<h4>Что это</h4>
<p><b>QuerySet</b> — ленивое представление SQL-запроса в Django ORM. Методы <code>filter()</code>, <code>exclude()</code>, <code>order_by()</code> возвращают новый QuerySet и обычно не ходят в БД сразу.</p>
<h4>Как работает в SQL</h4>
<p><code>filter()</code> добавляет условия <code>WHERE</code>, <code>exclude()</code> добавляет отрицание условия (NOT). Цепочка методов компилируется в один SQL.</p>
<h4>Типовые ошибки</h4>
<ul><li>Считать, что QuerySet мутируется на месте.</li><li>Рано выполнять запрос через <code>list()</code>/<code>len()</code> без необходимости.</li><li>Путать <code>exclude(a=1, b=2)</code> и <code>exclude(a=1).exclude(b=2)</code>.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>Book.objects.all()</code></li><li><code>Book.objects.filter(is_published=True)</code></li><li><code>Book.objects.exclude(price__isnull=True)</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/topics/db/queries/" target="_blank">Making queries</a> — базовые принципы QuerySet и ленивых вычислений.</p>
""",
        'tasks': _tasks([
            ('Верни все книги.', 'Book.objects.all()'),
            ('Верни все опубликованные книги.', 'Book.objects.filter(is_published=True)'),
            ('Верни неопубликованные книги.', 'Book.objects.filter(is_published=False)'),
            ('Верни книги, исключая неопубликованные.', 'Book.objects.exclude(is_published=False)'),
            ('Верни активные издательства.', 'Publisher.objects.filter(is_active=True)', '', 'Publisher'),
            ('Верни авторов из России.', 'Author.objects.filter(country="Россия")', '', 'Author'),
            ('Верни отзывы с рейтингом 5.', 'Review.objects.filter(rating=5)', '', 'Review'),
            ('Верни книги с непустой датой публикации.', 'Book.objects.filter(published_at__isnull=False)'),
            ('Верни книги с пустой ценой.', 'Book.objects.filter(price__isnull=True)'),
            ('Верни категории со slug="django".', 'Category.objects.filter(slug="django")', '', 'Category'),
        ], 'Book'),
    },
    {
        'slug': 'lookups-advanced',
        'name': 'Lookups и поиск',
        'order': 2,
        'theory': """
<h4>Что это</h4>
<p><b>Lookup</b> — суффикс после поля: <code>field__lookup=value</code>. Он задает тип сравнения.</p>
<h4>Как работает в SQL</h4>
<p>Примеры соответствий: <code>__gt</code> → <code>&gt;</code>, <code>__in</code> → <code>IN (...)</code>, <code>__icontains</code> → <code>LIKE/ILIKE</code> в зависимости от БД.</p>
<h4>Типовые ошибки</h4>
<ul><li>Использовать <code>contains</code> там, где нужен <code>icontains</code>.</li><li>Передавать строку вместо списка в <code>__in</code>.</li><li>Путать <code>isnull=True</code> с пустой строкой <code>""</code>.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>price__gte=500</code></li><li><code>title__icontains="django"</code></li><li><code>id__in=[1,2,3]</code></li><li><code>published_at__isnull=False</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/ref/models/querysets/#field-lookups" target="_blank">Field lookups</a> — полный список lookup-выражений.</p>
""",
        'tasks': _tasks([
            ('Книги с ценой > 1000.', 'Book.objects.filter(price__gt=1000)'),
            ('Книги с ценой >= 500.', 'Book.objects.filter(price__gte=500)'),
            ('Книги, где title содержит "Python".', 'Book.objects.filter(title__contains="Python")'),
            ('Книги, где title начинается с "Django".', 'Book.objects.filter(title__startswith="Django")'),
            ('Книги, где pages в диапазоне 200..400.', 'Book.objects.filter(pages__range=(200, 400))'),
            ('Издательства с founded_year в [1978, 1991].', 'Publisher.objects.filter(founded_year__in=[1978, 1991])', '', 'Publisher'),
            ('Отзывы с рейтингом < 4.', 'Review.objects.filter(rating__lt=4)', '', 'Review'),
            ('Авторы с непустым birth_year.', 'Author.objects.filter(birth_year__isnull=False)', '', 'Author'),
            ('BLE-метки, где ble_number содержит "002" без учета регистра.', 'BleTag.objects.filter(ble_number__icontains="002")', '', 'BleTag'),
            ('BLE-метки, где charge_value <= 15.', 'BleTag.objects.filter(charge_value__lte=15)', '', 'BleTag'),
        ], 'Book'),
    },
    {
        'slug': 'relations-joins',
        'name': 'Связи и JOIN через __',
        'order': 3,
        'theory': """
<h4>Что это</h4>
<p>Навигация по связям через двойное подчеркивание: <code>related__field</code>. Работает для FK, OneToOne, reverse-связей, M2M.</p>
<h4>Как работает в SQL</h4>
<p>Django строит нужные <code>JOIN</code> автоматически. Ты описываешь путь по связям, ORM собирает SQL.</p>
<h4>Типовые ошибки</h4>
<ul><li>Забывать <code>distinct()</code> при фильтрации по reverse/M2M и получать дубли.</li><li>Неверный <code>related_name</code> в обратной связи (подробнее — раздел «Обратные связи и related_name»).</li><li>Пытаться фильтровать по объекту, когда нужен путь к полю.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>Book.objects.filter(author__country="Россия")</code></li><li><code>Review.objects.filter(book__publisher__country="США")</code></li><li><code>Publisher.objects.filter(books__is_published=True).distinct()</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/topics/db/queries/#lookups-that-span-relationships" target="_blank">Lookups that span relationships</a> — фильтрация через связи.</p>
""",
        'tasks': _tasks([
            ('Книги, у которых автор из России.', 'Book.objects.filter(author__country="Россия")'),
            ('Книги, изданные в "Питер".', 'Book.objects.filter(publisher__name="Питер")'),
            ('Отзывы к опубликованным книгам.', 'Review.objects.filter(book__is_published=True)', '', 'Review'),
            ('Авторы с верифицированным профилем.', 'Author.objects.filter(profile__verified=True)', '', 'Author'),
            ('Книги без автора.', 'Book.objects.filter(author__isnull=True)'),
            ('BLE-метки с маршрутом "Маршрут А".', 'BleTag.objects.filter(ble_route__title="Маршрут А")', '', 'BleTag'),
            ('BLE-метки с площадкой "Площадка Север".', 'BleTag.objects.filter(construction_site__title="Площадка Север")', '', 'BleTag'),
            ('Орг.объекты, привязанные к площадке с title содержит "Север".', 'OrgObject.objects.filter(construction_site__title__icontains="север")', '', 'OrgObject'),
            ('Площадки, у которых есть BLE-метки.', 'ConstructionSite.objects.filter(ble_tags__isnull=False).distinct()', '', 'ConstructionSite'),
            ('Маршруты, у которых есть метки со статусом "установлена, работает".', 'BleRoute.objects.filter(ble_tags__status=1).distinct()', '', 'BleRoute'),
        ], 'Book'),
    },
    {
        'slug': 'reverse-relations-related-name',
        'name': 'Обратные связи и related_name',
        'order': 4,
        'theory': """
<h4>Что это</h4>
<p>С модели <b>A</b>, на которую ссылается <code>ForeignKey</code>/<code>OneToOne</code>/<code>ManyToMany</code> с модели <b>B</b>, можно попасть ко <b>всем B</b> через <b>обратный менеджер</b>. Имя этого атрибута задаётся в <code>related_name</code> у поля на стороне B; если его нет, Django создаёт имя по умолчанию: <code>&lt;имя_модели_B&gt;_set</code> в нижнем регистре (для нашей учебной модели <code>Shelf</code> с полем <code>book</code> у книги будет <code>shelf_set</code>).</p>
<p>В <b>фильтрах QuerySet</b> используется то же имя, что и у обратного менеджера: <code>Publisher.objects.filter(books__title__icontains="Django")</code> или <code>Book.objects.filter(shelf__label="A")</code> для связи без <code>related_name</code>.</p>
<h4>ManyToMany</h4>
<p>У M2M обе стороны симметричны в SQL через промежуточную таблицу; на стороне модели, где объявлено поле, обычно задают <code>related_name</code> для второй стороны. У нас у <code>Book.categories</code> указано <code>related_name="books"</code> — с категории: <code>category.books</code> и <code>Category.objects.filter(books__...)</code>.</p>
<h4>Как работает в SQL</h4>
<p>Цепочка <code>parent__child__field</code> превращается в JOIN по внешним ключам (и при необходимости DISTINCT, если из-за связей одна строка родителя размножается).</p>
<h4>Типовые ошибки</h4>
<ul><li>Путать имя поля на стороне потомка (<code>book</code>) и имя обратного доступа у родителя (<code>shelf_set</code> / <code>books</code>).</li><li>Забывать <code>distinct()</code>, когда фильтр по reverse или M2M даёт дубли pk.</li><li>Опечатка в <code>related_name</code> из модели — ORM сразу подскажет, что атрибут не существует.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li>С <code>related_name="books"</code>: <code>Author.objects.filter(books__is_published=True)</code></li><li>Без <code>related_name</code>: <code>Book.objects.filter(shelf__label="Витрина-A")</code></li><li>M2M: <code>Book.objects.filter(categories__slug="python")</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/topics/db/queries/#lookups-that-span-relationships" target="_blank">Lookups that span relationships</a> и <a href="https://docs.djangoproject.com/en/stable/ref/models/fields/#django.db.models.ForeignKey.related_name" target="_blank">ForeignKey.related_name</a>.</p>
""",
        'tasks': _tasks([
            (
                '<p>Модель <code>Book</code>. У <code>Shelf</code> к книге FK <b>без</b> <code>related_name</code> — обратный доступ с книги: <code>shelf_set</code>, в фильтрах: <code>shelf</code>.</p><p>Верни книги, у которых есть хотя бы одна связанная полка.</p>',
                'Book.objects.filter(shelf__isnull=False).distinct().order_by("id")',
                '',
                'Book',
            ),
            (
                '<p>Книги, у которых есть полка с меткой, содержащей «Витрина» (через обратную связь <code>shelf</code>).</p>',
                'Book.objects.filter(shelf__label__icontains="Витрина").distinct().order_by("id")',
                '',
                'Book',
            ),
            (
                '<p>Книги с полкой с точной меткой <code>Склад-B</code>.</p>',
                'Book.objects.filter(shelf__label="Склад-B").distinct().order_by("id")',
                '',
                'Book',
            ),
            (
                '<p>Модель <code>Shelf</code>. Все полки, привязанные к книгам, в названии которых есть «ORM».</p>',
                'Shelf.objects.filter(book__title__icontains="ORM").order_by("id")',
                '',
                'Shelf',
            ),
            (
                '<p>Издательства (<code>Publisher</code>), у которых есть хотя бы одна опубликованная книга. Обратная связь от книги к издательству: <code>related_name="books"</code>.</p>',
                'Publisher.objects.filter(books__is_published=True).distinct().order_by("id")',
                '',
                'Publisher',
            ),
            (
                '<p>Издательства, у которых есть книга с ценой строго больше 1000.</p>',
                'Publisher.objects.filter(books__price__gt=1000).distinct().order_by("id")',
                '',
                'Publisher',
            ),
            (
                '<p>Авторы, у которых есть книга с отзывом с рейтингом 5 (цепочка: автор → <code>books</code> → <code>reviews</code>).</p>',
                'Author.objects.filter(books__reviews__rating=5).distinct().order_by("id")',
                '',
                'Author',
            ),
            (
                '<p>Категории, в которых есть книга автора из России.</p>',
                'Category.objects.filter(books__author__country="Россия").distinct().order_by("id")',
                '',
                'Category',
            ),
            (
                '<p>Книги, относящиеся к категории со <code>slug="django"</code> (M2M, обратное имя с категории — <code>books</code>).</p>',
                'Book.objects.filter(categories__slug="django").distinct().order_by("id")',
                '',
                'Book',
            ),
            (
                '<p>Книги, которые одновременно в категории <code>python</code> и имеют хотя бы одну полку <code>Shelf</code>.</p>',
                'Book.objects.filter(categories__slug="python", shelf__isnull=False).distinct().order_by("id")',
                '',
                'Book',
            ),
            (
                '<p>Отзывы (<code>Review</code>), у которых у книги число страниц больше 300.</p>',
                'Review.objects.filter(book__pages__gt=300).order_by("id")',
                '',
                'Review',
            ),
            (
                '<p>Отзывы, у которых издательство книги в названии содержит «Reilly» (без учёта регистра).</p>',
                'Review.objects.filter(book__publisher__name__icontains="reilly").order_by("id")',
                '',
                'Review',
            ),
            (
                '<p>Издательства, у которых есть книга, стоящая на полке с меткой <code>Резерв</code> (цепочка <code>books</code> → <code>shelf</code>).</p>',
                'Publisher.objects.filter(books__shelf__label="Резерв").distinct().order_by("id")',
                '',
                'Publisher',
            ),
            (
                '<p>Компании, у которых есть BLE-метка со статусом «установлена, работает» (<code>status=1</code>). Обратное имя от <code>BleTag.company</code>: <code>ble_tags</code>.</p>',
                'Company.objects.filter(ble_tags__status=1).distinct().order_by("id")',
                '',
                'Company',
            ),
            (
                '<p>Компании, у которых есть площадка (<code>construction_sites</code>), в названии которой есть «Север».</p>',
                'Company.objects.filter(construction_sites__title__icontains="Север").distinct().order_by("id")',
                '',
                'Company',
            ),
            (
                '<p>Площадки, у которых есть хотя бы один орг.объект (<code>org_objects</code>).</p>',
                'ConstructionSite.objects.filter(org_objects__isnull=False).distinct().order_by("id")',
                '',
                'ConstructionSite',
            ),
            (
                '<p>Маршруты (<code>BleRoute</code>), у которых в <code>group_dates</code> есть запись на <b>сегодняшнюю</b> дату.</p>',
                'BleRoute.objects.filter(group_dates__dt=timezone.now().date()).distinct().order_by("id")',
                TZ_TASK_NOTE,
                'BleRoute',
            ),
            (
                '<p>Группы (<code>BleGroup</code>), у которых в <code>route_dates</code> есть запись на сегодня.</p>',
                'BleGroup.objects.filter(route_dates__dt=timezone.now().date()).distinct().order_by("id")',
                TZ_TASK_NOTE,
                'BleGroup',
            ),
            (
                '<p>BLE-метки, у которых есть хотя бы одна запись обхода (<code>inspection_records</code>).</p>',
                'BleTag.objects.filter(inspection_records__isnull=False).distinct().order_by("id")',
                '',
                'BleTag',
            ),
            (
                '<p>Орг.объекты, у которых есть хотя бы один таймшит-план (<code>timesheet_plans</code>).</p>',
                'OrgObject.objects.filter(timesheet_plans__isnull=False).distinct().order_by("id")',
                '',
                'OrgObject',
            ),
            (
                '<p>Авторы с верифицированным профилем (<code>profile__verified=True</code>), у которых есть книга с полкой.</p>',
                'Author.objects.filter(profile__verified=True, books__shelf__isnull=False).distinct().order_by("id")',
                '',
                'Author',
            ),
            (
                '<p>Книги, у которых есть отзыв с рейтингом не ниже 4.</p>',
                'Book.objects.filter(reviews__rating__gte=4).distinct().order_by("id")',
                '',
                'Book',
            ),
            (
                '<p>Категории, в которых есть книга, название которой начинается с «Django».</p>',
                'Category.objects.filter(books__title__startswith="Django").distinct().order_by("id")',
                '',
                'Category',
            ),
            (
                '<p>BLE-метки на площадке, где есть другая метка со статусом 1 (фильтр через <code>construction_site__ble_tags</code>).</p>',
                'BleTag.objects.filter(construction_site__ble_tags__status=1).distinct().order_by("id")',
                '',
                'BleTag',
            ),
            (
                '<p>Компании, у которых есть BLE-метка, привязанная к площадке с «Юг» в названии.</p>',
                'Company.objects.filter(ble_tags__construction_site__title__icontains="Юг").distinct().order_by("id")',
                '',
                'Company',
            ),
            (
                '<p>Маршруты, у которых есть метка с <code>bypass_status=1</code> (через <code>ble_tags</code>).</p>',
                'BleRoute.objects.filter(ble_tags__bypass_status=1).distinct().order_by("id")',
                '',
                'BleRoute',
            ),
            (
                '<p>Книги без автора (<code>author</code> пуст), но с хотя бы одним отзывом — через обратную связь <code>reviews</code>.</p>',
                'Book.objects.filter(author__isnull=True, reviews__isnull=False).distinct().order_by("id")',
                '',
                'Book',
            ),
        ], 'Book'),
    },
    {
        'slug': 'q-logic',
        'name': 'Q-логика: AND / OR / NOT',
        'order': 5,
        'theory': """
<h4>Что это</h4>
<p><code>Q</code> — объект логических выражений для ORM. Нужен для OR, NOT и сложных комбинаций условий.</p>
<h4>Как работает в SQL</h4>
<p><code>&amp;</code>, <code>|</code>, <code>~</code> превращаются в булевы выражения SQL с правильными скобками.</p>
<h4>Типовые ошибки</h4>
<ul><li>Отсутствие скобок в длинных выражениях.</li><li>Смешение приоритетов <code>&amp;</code> и <code>|</code>.</li><li>Попытка передать Python <code>or/and</code> вместо <code>|/&amp;</code>.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>Q(a=1) | Q(b=2)</code></li><li><code>Q(a=1) &amp; ~Q(c__isnull=True)</code></li><li><code>Model.objects.filter(Q(...), is_active=True)</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/topics/db/queries/#complex-lookups-with-q-objects" target="_blank">Complex lookups with Q objects</a> — сложные условия.</p>
""",
        'tasks': _tasks([
            ('Книги: опубликованы И цена > 500.', 'Book.objects.filter(Q(is_published=True) & Q(price__gt=500))'),
            ('Книги: pages > 300 ИЛИ price < 700.', 'Book.objects.filter(Q(pages__gt=300) | Q(price__lt=700))'),
            ('Авторы из России или США.', 'Author.objects.filter(Q(country="Россия") | Q(country="США"))', '', 'Author'),
            ('Книги с непустой ценой через ~Q.', 'Book.objects.filter(~Q(price__isnull=True))'),
            ('BLE: статус installed_working И charge <= 15.', 'BleTag.objects.filter(Q(status=1) & Q(charge_value__lte=15))', '', 'BleTag'),
            ('BLE: bypass_status=1 ИЛИ charge <= 15.', 'BleTag.objects.filter(Q(bypass_status=1) | Q(charge_value__lte=15))', '', 'BleTag'),
            ('BLE: НЕ status=IN_STOCK.', 'BleTag.objects.filter(~Q(status=3))', '', 'BleTag'),
            ('BLE: (status=1 и route не null) или (status=2 и route is null).', 'BleTag.objects.filter((Q(status=1) & Q(ble_route__isnull=False)) | (Q(status=2) & Q(ble_route__isnull=True)))', '', 'BleTag'),
            ('Книги: опубликованы и (цена > 800 или pages < 150).', 'Book.objects.filter(Q(is_published=True) & (Q(price__gt=800) | Q(pages__lt=150)))'),
            ('BLE: ble_number содержит "BLE" и mac_address содержит "02".', 'BleTag.objects.filter(Q(ble_number__icontains="ble") & Q(mac_address__icontains="02"))', '', 'BleTag'),
        ], 'Book'),
    },
    {
        'slug': 'f-expressions',
        'name': 'F-выражения: сравнение полей и вычисления',
        'order': 6,
        'theory': """
<h4>Что это</h4>
<p><code>F()</code> — ссылка на значение поля прямо в SQL-выражении. Нужна, когда сравниваешь поле с полем или считаешь новое значение от текущего.</p>
<h4>Как работает в SQL</h4>
<p><code>F("a")</code> компилируется в имя колонки. Пример: <code>filter(charge_value__lte=F("power"))</code> станет сравнением двух колонок в SQL.</p>
<h4>Типовые ошибки</h4>
<ul>
<li>Писать <code>F("charge_value__lte") = 15</code> — так нельзя.</li>
<li>Смешивать тему F и тему Case/When слишком рано.</li>
<li>Использовать F там, где нужно константное значение.</li>
</ul>
<h4>Мини-шпаргалка</h4>
<ul>
<li><code>BleTag.objects.filter(charge_value__lte=F("power"))</code></li>
<li><code>BleTag.objects.annotate(double_power=F("power") * 2)</code></li>
<li><code>BleTag.objects.filter(charge_value__lte=F("power") + 5)</code></li>
</ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/ref/models/expressions/#f-expressions" target="_blank">F() expressions</a> — официальные примеры сравнения полей и вычислений.</p>
""",
        'tasks': _tasks([
            ('BLE-метки, где charge_value меньше либо равен power (сравнение поле-к-полю через F).', 'BleTag.objects.filter(charge_value__lte=F("power"))', '', 'BleTag'),
            ('BLE-метки, где charge_value больше power.', 'BleTag.objects.filter(charge_value__gt=F("power"))', '', 'BleTag'),
            ('Аннотируй BLE полем power_copy через F("power").', 'BleTag.objects.annotate(power_copy=F("power"))', '', 'BleTag'),
            ('Аннотируй BLE полем double_power = power * 2.', 'BleTag.objects.annotate(double_power=F("power") * 2)', '', 'BleTag'),
            ('Аннотируй BLE нормализованной мощностью norm_power = power + frequency.', 'BleTag.objects.annotate(norm_power=F("power") + F("frequency"))', '', 'BleTag'),
            ('Отфильтруй книги, где pages >= price (учебное сравнение полей через F).', 'Book.objects.filter(pages__gte=F("price"))', '', 'Book'),
            ('Аннотируй книги delta = pages - 100.', 'Book.objects.annotate(delta=F("pages") - 100)', '', 'Book'),
            ('BLE: route есть, и charge_value <= power + 5 (через F и арифметику).', 'BleTag.objects.filter(ble_route__isnull=False, charge_value__lte=F("power") + 5)', '', 'BleTag'),
            ('Аннотируй BLE effective_power = power - frequency.', 'BleTag.objects.annotate(effective_power=F("power") - F("frequency"))', '', 'BleTag'),
            ('BLE: где power равен frequency (через F).', 'BleTag.objects.filter(power=F("frequency"))', '', 'BleTag'),
            ('Аннотируй книги ratio_like = pages + price.', 'Book.objects.annotate(ratio_like=F("pages") + F("price"))', '', 'Book'),
            ('BLE: где charge_value >= power - 3.', 'BleTag.objects.filter(charge_value__gte=F("power") - 3)', '', 'BleTag'),
        ], 'BleTag'),
    },
    {
        'slug': 'value-expressions',
        'name': 'Value: константы в выражениях ORM',
        'order': 7,
        'theory': """
<h4>Что это</h4>
<p><code>Value(...)</code> оборачивает Python-значение в SQL-выражение. Используется внутри <code>annotate</code>, <code>Case/When</code>, <code>Coalesce</code> и других выражений.</p>
<h4>Как работает в SQL</h4>
<p><code>Value("text")</code>, <code>Value(True)</code>, <code>Value(0)</code> превращаются в литералы SQL нужного типа.</p>
<h4>Типовые ошибки</h4>
<ul><li>Писать <code>then=True</code> вместо <code>then=Value(True)</code> в сложных выражениях.</li><li>Не указывать <code>output_field</code> там, где Django не может вывести тип сам.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>Coalesce(F("ble_route__title"), Value("без маршрута"))</code></li><li><code>Case(..., default=Value(False), output_field=BooleanField())</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/ref/models/expressions/#value-expressions" target="_blank">Value() expressions</a>.</p>
""",
        'tasks': _tasks([
            ('Аннотируй BLE строкой source="manual" через Value.', 'BleTag.objects.annotate(source=Value("manual"))', '', 'BleTag'),
            ('Аннотируй BLE числом threshold=15 через Value.', 'BleTag.objects.annotate(threshold=Value(15))', '', 'BleTag'),
            ('Аннотируй BLE route_title_safe: route title или "без маршрута".', 'BleTag.objects.annotate(route_title_safe=Coalesce(F("ble_route__title"), Value("без маршрута")))', '', 'BleTag'),
            ('Аннотируй BLE флагом always_true через Value(True).', 'BleTag.objects.annotate(always_true=Value(True))', '', 'BleTag'),
            ('Аннотируй BLE low_charge: True если charge<=15 иначе False (Case + Value).', 'BleTag.objects.annotate(low_charge=Case(When(charge_value__lte=15, then=Value(True)), default=Value(False), output_field=BooleanField()))', '', 'BleTag'),
            ('Аннотируй BLE status_label: "working" если status=1 иначе "other".', 'BleTag.objects.annotate(status_label=Case(When(status=1, then=Value("working")), default=Value("other"), output_field=CharField()))', '', 'BleTag'),
            ('Аннотируй книги safe_price: price или 0 через Coalesce + Value.', 'Book.objects.annotate(safe_price=Coalesce(F("price"), Value(0)))', '', 'Book'),
            ('Аннотируй маршруты title_or_default: title или "no-title".', 'BleRoute.objects.annotate(title_or_default=Coalesce(F("title"), Value("no-title")))', '', 'BleRoute'),
            ('Аннотируй BLE status_bool: True если status=1 иначе False.', 'BleTag.objects.annotate(status_bool=Case(When(status=1, then=Value(True)), default=Value(False), output_field=BooleanField()))', '', 'BleTag'),
            ('Аннотируй BLE текстовой меткой label="tag" через Value.', 'BleTag.objects.annotate(label=Value("tag"))', '', 'BleTag'),
        ], 'BleTag'),
    },
    {
        'slug': 'annotate-case-f',
        'name': 'Annotate и Case/When',
        'order': 8,
        'theory': """
<h4>Что это</h4>
<p><code>annotate()</code> добавляет вычисляемые поля к каждой строке, <code>F()</code> ссылается на поля модели, <code>Case/When</code> позволяет ветвить логику.</p>
<h4>Как работает в SQL</h4>
<p><code>annotate</code> обычно добавляет выражения в SELECT (и при необходимости GROUP BY), <code>Case/When</code> компилируется в SQL <code>CASE WHEN</code>.</p>
<h4>Типовые ошибки</h4>
<ul><li>Фильтрация по аннотации до её создания.</li><li>Отсутствие <code>output_field</code> в сложных выражениях.</li><li>Непонимание, когда появляется GROUP BY.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>annotate(cnt=Count("reviews"))</code></li><li><code>annotate(flag=Case(..., output_field=BooleanField()))</code></li><li><code>annotate(route_title=Coalesce(F("ble_route__title"), Value("без маршрута")))</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/topics/db/aggregation/" target="_blank">Aggregation</a> и <a href="https://docs.djangoproject.com/en/stable/ref/models/conditional-expressions/" target="_blank">Conditional expressions</a>.</p>
""",
        'tasks': _tasks([
            ('Аннотируй книги количеством отзывов в поле cnt.', 'Book.objects.annotate(cnt=Count("reviews"))'),
            ('Аннотируй авторов количеством книг в поле books_count.', 'Author.objects.annotate(books_count=Count("books"))', '', 'Author'),
            ('Аннотируй BLE-маршруты количеством меток в поле tag_count.', 'BleRoute.objects.annotate(tag_count=Count("ble_tags"))', '', 'BleRoute'),
            ('BLE-метки с аннотацией low_charge: True если charge_value<=15 иначе False.', 'BleTag.objects.annotate(low_charge=Case(When(charge_value__lte=15, then=Value(True)), default=Value(False), output_field=BooleanField()))', '', 'BleTag'),
            ('BLE-метки с аннотацией route_title_safe: route title или "без маршрута".', 'BleTag.objects.annotate(route_title_safe=Coalesce(F("ble_route__title"), Value("без маршрута"))) ', '', 'BleTag'),
            ('Книги со средней оценкой отзывов в поле avg_rating.', 'Book.objects.annotate(avg_rating=Avg("reviews__rating"))'),
            ('BLE-метки с has_route: True если ble_route не null.', 'BleTag.objects.annotate(has_route=Case(When(ble_route__isnull=False, then=Value(True)), default=Value(False), output_field=BooleanField()))', '', 'BleTag'),
            ('Аннотируй площадки количеством меток tags_count и оставь только tags_count>0.', 'ConstructionSite.objects.annotate(tags_count=Count("ble_tags")).filter(tags_count__gt=0)', '', 'ConstructionSite'),
            ('Аннотируй BLE-метки мощностью в поле same_power через F("power").', 'BleTag.objects.annotate(same_power=F("power"))', '', 'BleTag'),
            ('Аннотируй маршруты has_working_tag через Case+Count (если есть рабочая метка, то True).', 'BleRoute.objects.annotate(working_count=Count("ble_tags", filter=Q(ble_tags__status=1))).annotate(has_working_tag=Case(When(working_count__gt=0, then=Value(True)), default=Value(False), output_field=BooleanField()))', '', 'BleRoute'),
        ], 'Book'),
    },
    {
        'slug': 'grouping-values-annotate',
        'name': 'Группировка: annotate и values',
        'order': 9,
        'theory': """
<h4>Что это</h4>
<p><b>Агрегация по строкам модели:</b> <code>Model.objects.annotate(cnt=Count("children"))</code> — к каждой строке добавляется число связанных записей; в SQL это JOIN + подсчёт по группам с ключом <code>id</code> основной таблицы.</p>
<p><b>Группировка по произвольным полям:</b> цепочка <code>values("поле1", ...).annotate(агрегат=...)</code> задаёт столбцы <code>GROUP BY</code>: одна строка результата на каждое уникальное сочетание этих полей. Так же устроены «внутренние» подзапросы в <code>Subquery(...)</code> с <code>values(...).annotate(...).values("одна_колонка")</code>.</p>
<h4>Как работает в SQL</h4>
<p><code>annotate</code> без предшествующего <code>values()</code> обычно оставляет по одной строке на объект модели. После <code>values("publisher_id")</code> ORM генерирует <code>SELECT publisher_id, COUNT(...) ... GROUP BY publisher_id</code>.</p>
<h4>Типовые ошибки</h4>
<ul><li>Смешивать в одном <code>values()</code> поля, по которым не нужна группировка, и забыть, что остальные колонки «схлопнутся».</li><li>Фильтровать по аннотации до <code>annotate</code>.</li><li>Для сравнения с эталоном в задачах с <code>values()</code> задавай тот же набор полей и тот же <code>order_by</code>, что в формулировке.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>Author.objects.annotate(n=Count("books"))</code></li><li><code>Book.objects.values("publisher_id").annotate(bc=Count("id")).order_by("publisher_id")</code></li><li><code>Model.objects.values("a").annotate(m=Max("b")).filter(m__gt=0)</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/topics/db/aggregation/" target="_blank">Aggregation</a> и раздел про <code>values()</code> + annotate в той же статье.</p>
""",
        'tasks': _tasks([
            (
                '<p>Модель <code>BleInspectionRecord</code>. По каждому значению <code>ble_id</code> посчитай, сколько строк обходов относится к этой метке, и положи результат в аннотацию <code>n</code>.</p>'
                '<ul><li>группировка: <code>values("ble_id")</code></li>'
                '<li>подсчёт: <code>annotate(n=Count("id"))</code></li>'
                '<li>порядок строк: <code>order_by("ble_id")</code></li></ul>',
                'BleInspectionRecord.objects.values("ble_id").annotate(n=Count("id")).order_by("ble_id")',
                '',
                'BleInspectionRecord',
            ),
            ('По каждому <code>publisher_id</code> посчитай число книг в поле <code>bc</code> (order_by по publisher_id).', 'Book.objects.values("publisher_id").annotate(bc=Count("id")).order_by("publisher_id")', '', 'Book'),
            ('По каждому <code>status</code> BLE посчитай метки в поле <code>cnt</code> (order_by по status).', 'BleTag.objects.values("status").annotate(cnt=Count("id")).order_by("status")', '', 'BleTag'),
            ('Аннотируй издательства числом книг <code>book_n</code> (без values), order_by по id.', 'Publisher.objects.annotate(book_n=Count("books")).order_by("id")', '', 'Publisher'),
            ('Аннотируй категории числом книг <code>bn</code>, оставь только с <code>bn &gt; 0</code>, order_by по id.', 'Category.objects.annotate(bn=Count("books")).filter(bn__gt=0).order_by("id")', '', 'Category'),
            ('По полю <code>is_published</code> сгруппируй книги и посчитай их число в <code>n</code>, order_by по is_published.', 'Book.objects.values("is_published").annotate(n=Count("id")).order_by("is_published")', '', 'Book'),
            ('По <code>ble_route_id</code> посчитай BLE-метки в поле <code>c</code>, order_by по ble_route_id.', 'BleTag.objects.values("ble_route_id").annotate(c=Count("id")).order_by("ble_route_id")', '', 'BleTag'),
            ('По <code>company_id</code> площадок посчитай площадки в <code>cs_count</code>, order_by по company_id.', 'ConstructionSite.objects.values("company_id").annotate(cs_count=Count("id")).order_by("company_id")', '', 'ConstructionSite'),
            ('Аннотируй книги числом отзывов <code>rc</code>, оставь с <code>rc &gt;= 2</code>, order_by по id.', 'Book.objects.annotate(rc=Count("reviews")).filter(rc__gte=2).order_by("id")', '', 'Book'),
            ('Аннотируй маршруты числом меток <code>tag_n</code>, order_by по id.', 'BleRoute.objects.annotate(tag_n=Count("ble_tags")).order_by("id")', '', 'BleRoute'),
        ], 'Book'),
    },
    {
        'slug': 'subquery-outerref-exists',
        'name': 'Subquery, OuterRef, Exists',
        'order': 10,
        'theory': """
<h4>Что это</h4>
<p><code>Subquery</code> и <code>OuterRef</code> позволяют встроить коррелированный подзапрос, <code>Exists</code> — быстрый булев флаг наличия записей.</p>
<p><b>Связь с группировкой:</b> внутри <code>Subquery</code> часто встречается цепочка <code>values(...).annotate(...).values("одна_колонка")[:1]</code> — это та же идея, что в разделе «Группировка: annotate и values».</p>
<h4>Как работает в SQL</h4>
<p>ORM строит подзапрос вида <code>SELECT ... WHERE child.parent_id = outer.id</code>. <code>Exists</code> превращается в <code>EXISTS (subquery)</code>.</p>
<h4>Типовые ошибки</h4>
<ul><li>Subquery возвращает больше 1 колонки/строки.</li><li>Забыть <code>[:1]</code> для одиночного значения.</li><li>Неправильный путь поля в <code>OuterRef(...)</code>.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>Subquery(...values("field")[:1])</code></li><li><code>Exists(Model.objects.filter(parent_id=OuterRef("pk")))</code></li><li><code>annotate(last_dt=Subquery(...))</code></li></ul>
<h4>Дата «сегодня» и <code>timezone</code></h4>
<p>В задачах про «сегодня» эталон использует <code>timezone.now().date()</code>.</p>
<p><b>Что такое <code>timezone</code>:</b> это модуль <a href="https://docs.djangoproject.com/en/stable/ref/utils/#django.utils.timezone" target="_blank"><code>django.utils.timezone</code></a>. Он даёт «текущий момент» с учётом настроек Django (<code>USE_TZ</code>, <code>TIME_ZONE</code>), в отличие от «наивного» <code>datetime.now()</code>.</p>
<p><b>Откуда он в тренажёре:</b> при проверке кода в окружение уже подставлен объект <code>timezone</code> (как если бы вы написали <code>from django.utils import timezone</code>). Писать импорт в поле решения не обязательно.</p>
<p><b>Почему не <code>datetime.now().date()</code>:</b> при включённой таймзоне локальная дата может отличаться от «сегодня» в часовом поясе проекта — эталон и проверка завязаны на <code>timezone.now()</code>.</p>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/ref/models/expressions/#subquery-expressions" target="_blank">Subquery expressions</a> и <a href="https://docs.djangoproject.com/en/stable/ref/models/expressions/#exists-subqueries" target="_blank">Exists</a>.</p>
""",
        'tasks': _tasks([
            ('Аннотируй BLE-метки датой последнего обхода (last_record_dt) через Subquery+OuterRef.', 'BleTag.objects.annotate(last_record_dt=Subquery(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk")).values("ble_id").annotate(max_dt=Max("record_dt")).values("max_dt")[:1]))', SUBQUERY_SINGLE_COL_NOTE, 'BleTag'),
            ('Аннотируй BLE-метки флагом has_inspection_today через Exists.', 'BleTag.objects.annotate(has_inspection_today=Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__date=timezone.now().date())))', TZ_TASK_NOTE, 'BleTag'),
            ('Аннотируй маршруты флагом has_group_today через Exists(BleGroupRouteDate).', 'BleRoute.objects.annotate(has_group_today=Exists(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("pk"), dt=timezone.now().date())))', TZ_TASK_NOTE, 'BleRoute'),
            ('Аннотируй BLE-метки group_id на сегодня через Subquery(BleGroupRouteDate).', 'BleTag.objects.annotate(group_id=Subquery(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date()).order_by("-id").values("ble_group_id")[:1]))', TZ_TASK_NOTE, 'BleTag'),
            ('Аннотируй BLE-метки group_title на сегодня через Subquery.', 'BleTag.objects.annotate(group_title_today=Subquery(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date()).order_by("-id").values("ble_group__title")[:1]))', TZ_TASK_NOTE, 'BleTag'),
            ('Аннотируй BLE-метки org_object_id: последний объект по той же construction_site.', 'BleTag.objects.annotate(org_object_id=Subquery(OrgObject.objects.filter(construction_site=OuterRef("construction_site"), deleted__isnull=True).order_by("-id").values("id")[:1]))', '', 'BleTag'),
            ('Аннотируй OrgObject has_plan через Exists(TimesheetPlan).', 'OrgObject.objects.annotate(has_plan=Exists(TimesheetPlan.objects.filter(org_object_id=OuterRef("pk"))))', '', 'OrgObject'),
            ('Верни BLE, у которых есть обходы (через Exists в filter).', 'BleTag.objects.filter(Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"))))', '', 'BleTag'),
            ('Верни BLE, у которых нет обходов (через ~Exists в filter).', 'BleTag.objects.filter(~Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"))))', '', 'BleTag'),
            ('Аннотируй BLE max_record_dt и отсортируй по нему по убыванию.', 'BleTag.objects.annotate(max_record_dt=Subquery(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk")).values("ble_id").annotate(m=Max("record_dt")).values("m")[:1])).order_by("-max_record_dt", "id")', '', 'BleTag'),
        ], 'BleTag'),
    },
    {
        'slug': 'inspection-status-logic',
        'name': 'Case-ветки как в inspection_status',
        'order': 11,
        'theory': """
<h4>Что это</h4>
<p>Пошаговая сборка бизнес-статуса: сначала простые boolean-аннотации, затем объединение в итоговый статус через <code>Case/When</code>.</p>
<h4>Как работает в SQL</h4>
<p>Каждый промежуточный флаг — отдельное SQL-выражение, итог — CASE с несколькими WHEN и default.</p>
<h4>Типовые ошибки</h4>
<ul><li>Перепутанный порядок веток WHEN (ранние ветки перехватывают условия).</li><li>Смешение <code>isnull</code> и фактических boolean-флагов.</li><li>Отсутствие fallback/default.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>has_plan_today=Exists(...)</code></li><li><code>has_inspection_today=Exists(...)</code></li><li><code>inspection_status=Case(When(...), default=Value(False))</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/ref/models/conditional-expressions/" target="_blank">Conditional expressions</a> — правила работы Case/When.</p>
""",
        'tasks': _tasks([
            ('Аннотируй BLE has_plan_today через Exists(BleGroupRouteDate) на today.', 'BleTag.objects.annotate(has_plan_today=Exists(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date())))', '', 'BleTag'),
            ('Аннотируй BLE has_inspection_today через Exists(BleInspectionRecord today).', 'BleTag.objects.annotate(has_inspection_today=Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__date=timezone.now().date())))', '', 'BleTag'),
            ('Аннотируй BLE fallback_status=True, если есть обход за последние 2 дня.', 'BleTag.objects.annotate(fallback_status=Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__gte=timezone.now()-timedelta(days=2))))', '', 'BleTag'),
            ('Аннотируй BLE inspection_status: если route null -> False, иначе True.', 'BleTag.objects.annotate(inspection_status=Case(When(ble_route__isnull=True, then=Value(False)), default=Value(True), output_field=BooleanField()))', '', 'BleTag'),
            ('Аннотируй BLE inspection_status: если route null и group null -> True, если один из них null -> False, иначе True.', 'BleTag.objects.annotate(group_id_today=Subquery(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date()).values("ble_group_id")[:1])).annotate(inspection_status=Case(When(Q(ble_route__isnull=True) & Q(group_id_today__isnull=True), then=Value(True)), When(Q(ble_route__isnull=True) | Q(group_id_today__isnull=True), then=Value(False)), default=Value(True), output_field=BooleanField()))', '', 'BleTag'),
            ('Верни BLE, где inspection_status=False (вычисли его через Case: route null => False).', 'BleTag.objects.annotate(inspection_status=Case(When(ble_route__isnull=True, then=Value(False)), default=Value(True), output_field=BooleanField())).filter(inspection_status=False)', '', 'BleTag'),
            ('Верни BLE со статусом "установлена, работает" и has_plan_today=True.', 'BleTag.objects.annotate(has_plan_today=Exists(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date()))).filter(status=1, has_plan_today=True)', '', 'BleTag'),
            ('Верни BLE со статусом "установлена, работает", has_plan_today=True и has_inspection_today=False.', 'BleTag.objects.annotate(has_plan_today=Exists(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date())), has_inspection_today=Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__date=timezone.now().date()))).filter(status=1, has_plan_today=True, has_inspection_today=False)', '', 'BleTag'),
            ('Верни BLE для map_only: только status=installed_working.', 'BleTag.objects.filter(status=1)', '', 'BleTag'),
            ('Аннотируй BLE bypass_flag: True, если bypass_status=1 и status=1.', 'BleTag.objects.annotate(bypass_flag=Case(When(Q(bypass_status=1) & Q(status=1), then=Value(True)), default=Value(False), output_field=BooleanField()))', '', 'BleTag'),
        ], 'BleTag'),
    },
    {
        'slug': 'dynamic-filters',
        'name': 'Динамические фильтры (как параметры API)',
        'order': 12,
        'theory': """
<h4>Что это</h4>
<p>Динамические фильтры — это поэтапное добавление условий в QuerySet в зависимости от входных параметров API.</p>
<h4>Как работает в SQL</h4>
<p>Каждый дополнительный <code>filter()</code> расширяет WHERE. В конце ORM компилирует единый SQL.</p>
<h4>Типовые ошибки</h4>
<ul><li>Проверять <code>if param</code> для булевых значений (теряется <code>False</code>).</li><li>Фильтровать по неаннотированному полю.</li><li>Смешивать list и scalar в <code>__in</code>.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>if route_ids: qs = qs.filter(route_id__in=route_ids)</code></li><li><code>if flag is not None: qs = qs.filter(flag=flag)</code></li><li><code>qs = qs.filter(Q(a__icontains=s) | Q(b__icontains=s))</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/ref/models/querysets/#filter" target="_blank">QuerySet.filter()</a> и <a href="https://docs.djangoproject.com/en/stable/topics/db/queries/" target="_blank">Making queries</a>.</p>
""",
        'tasks': _tasks([
            ('BLE по конкретному id=1.', 'BleTag.objects.filter(pk=1)', '', 'BleTag'),
            ('BLE по списку площадок [1,2].', 'BleTag.objects.filter(construction_site_id__in=[1, 2])', '', 'BleTag'),
            ('BLE по списку маршрутов [1,2].', 'BleTag.objects.filter(ble_route_id__in=[1, 2])', '', 'BleTag'),
            ('BLE по списку групп [1]: сначала аннотируй group_id_today через Subquery, затем фильтр.', 'BleTag.objects.annotate(group_id_today=Subquery(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date()).order_by("-id").values("ble_group_id")[:1])).filter(group_id_today__in=[1])', '', 'BleTag'),
            ('BLE с low_charge_value=True: status=1 и charge<=15.', 'BleTag.objects.filter(status=1, charge_value__lte=15)', '', 'BleTag'),
            ('BLE с low_charge_value=False: status=1 и charge>15.', 'BleTag.objects.filter(status=1, charge_value__gt=15)', '', 'BleTag'),
            ('BLE bypass_status=1.', 'BleTag.objects.filter(bypass_status=1)', '', 'BleTag'),
            ('BLE с search_value="chip-00" по ble_number/mac_address/chip_uuid (icontains + OR).', 'BleTag.objects.filter(Q(ble_number__icontains="chip-00") | Q(mac_address__icontains="chip-00") | Q(chip_uuid__icontains="chip-00"))', '', 'BleTag'),
            ('BLE с непустой площадкой и маршрутом.', 'BleTag.objects.filter(construction_site__isnull=False, ble_route__isnull=False)', '', 'BleTag'),
            ('BLE без площадки И без маршрута.', 'BleTag.objects.filter(construction_site__isnull=True, ble_route__isnull=True)', '', 'BleTag'),
        ], 'BleTag'),
    },
    {
        'slug': 'sorting-mapping',
        'name': 'Сортировка и sort-mapping',
        'order': 13,
        'theory': """
<h4>Что это</h4>
<p>Динамическая сортировка строится через map безопасных колонок и <code>order_by()</code>.</p>
<h4>Как работает в SQL</h4>
<p><code>order_by("field")</code> → <code>ORDER BY field ASC</code>, <code>order_by("-field")</code> → DESC.</p>
<h4>Типовые ошибки</h4>
<ul><li>Подставлять сырую строку от клиента в <code>order_by</code> без whitelist.</li><li>Не задавать второй стабильный ключ сортировки.</li><li>Сортировать по полю, которого нет в annotate/select.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>qs.order_by(field, "id")</code></li><li><code>qs.order_by("-" + field, "id")</code></li><li><code>qs.order_by("-record_dt", "id")</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/ref/models/querysets/#order-by" target="_blank">order_by()</a>.</p>
""",
        'tasks': _tasks([
            ('Отсортируй BLE по ble_number, затем id.', 'BleTag.objects.order_by("ble_number", "id")', '', 'BleTag'),
            ('Отсортируй BLE по статусу по убыванию, затем id.', 'BleTag.objects.order_by("-status", "id")', '', 'BleTag'),
            ('Отсортируй BLE по charge_value по возрастанию, затем id.', 'BleTag.objects.order_by("charge_value", "id")', '', 'BleTag'),
            ('Отсортируй BLE по charge_value по убыванию, затем id.', 'BleTag.objects.order_by("-charge_value", "id")', '', 'BleTag'),
            ('Отсортируй BLE по record_dt (через аннотацию max обхода) по убыванию, затем id.', 'BleTag.objects.annotate(record_dt=Subquery(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk")).values("ble_id").annotate(m=Max("record_dt")).values("m")[:1])).order_by("-record_dt", "id")', '', 'BleTag'),
            ('Отсортируй BLE по created_at по убыванию.', 'BleTag.objects.order_by("-created_at", "id")', '', 'BleTag'),
            ('Отсортируй BLE по mac_address по возрастанию.', 'BleTag.objects.order_by("mac_address", "id")', '', 'BleTag'),
            ('Отсортируй BLE по мощности power по убыванию.', 'BleTag.objects.order_by("-power", "id")', '', 'BleTag'),
            ('Отсортируй BLE по hardware_version, затем ble_number.', 'BleTag.objects.order_by("hardware_version", "ble_number", "id")', '', 'BleTag'),
            ('Отсортируй книги по price по убыванию и title по возрастанию.', 'Book.objects.order_by("-price", "title")', '', 'Book'),
        ], 'BleTag'),
    },
    {
        'slug': 'performance-prefetch',
        'name': 'Оптимизация: select_related/prefetch_related',
        'order': 14,
        'theory': """
<h4>Что это</h4>
<p><code>select_related</code> и <code>prefetch_related</code> — ключевые методы оптимизации ORM-запросов.</p>
<h4>Как работает в SQL</h4>
<p><code>select_related</code> делает JOIN в одном SQL (FK/OneToOne), <code>prefetch_related</code> выполняет дополнительные SQL и связывает данные в Python (reverse/M2M).</p>
<h4>Типовые ошибки</h4>
<ul><li>Использовать <code>select_related</code> для M2M.</li><li>Не префетчить reverse связи и ловить N+1.</li><li>Префетчить «всё подряд» без необходимости.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li><code>Book.objects.select_related("author")</code></li><li><code>Book.objects.prefetch_related("categories")</code></li><li><code>BleTag.objects.select_related("ble_route").prefetch_related("inspection_records")</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related" target="_blank">select_related()</a> и <a href="https://docs.djangoproject.com/en/stable/ref/models/querysets/#prefetch-related" target="_blank">prefetch_related()</a>.</p>
""",
        'tasks': _tasks([
            ('Книги с автором и издательством через select_related.', 'Book.objects.select_related("author", "publisher")', '', 'Book'),
            ('Отзывы с книгой и автором книги через select_related.', 'Review.objects.select_related("book", "book__author")', '', 'Review'),
            ('BLE-метки с route и construction_site через select_related.', 'BleTag.objects.select_related("ble_route", "construction_site")', '', 'BleTag'),
            ('Площадки с org_objects и ble_tags через prefetch_related.', 'ConstructionSite.objects.prefetch_related("org_objects", "ble_tags")', '', 'ConstructionSite'),
            ('Маршруты с метками и group_dates через prefetch_related.', 'BleRoute.objects.prefetch_related("ble_tags", "group_dates")', '', 'BleRoute'),
            ('OrgObject с timesheet_plans через prefetch_related.', 'OrgObject.objects.prefetch_related("timesheet_plans")', '', 'OrgObject'),
            ('BLE-записи обхода с меткой через select_related.', 'BleInspectionRecord.objects.select_related("ble")', '', 'BleInspectionRecord'),
            ('BLE-метки с route через select_related и обходами через prefetch_related.', 'BleTag.objects.select_related("ble_route").prefetch_related("inspection_records")', '', 'BleTag'),
            ('Авторы с профилем и книгами (select_related+prefetch_related).', 'Author.objects.select_related("profile").prefetch_related("books")', '', 'Author'),
            ('Издательства с книгами, а книги с отзывами (двойной prefetch).', 'Publisher.objects.prefetch_related("books__reviews")', '', 'Publisher'),
        ], 'BleTag'),
    },
    {
        'slug': 'master-ble-query-builder',
        'name': 'Мастер-сборка BLE-запроса по шагам',
        'order': 15,
        'theory': """
<h4>Что это</h4>
<p>Capstone-блок: собираем сложный QuerySet из независимых шагов — от базовой выборки до динамической фильтрации и сортировки.</p>
<h4>Как работает в SQL</h4>
<p>Это один композитный запрос: JOIN + CASE + EXISTS + Subquery + ORDER BY. ORM даёт все эти конструкции без raw SQL.</p>
<h4>Типовые ошибки</h4>
<ul><li>Пытаться сделать всё в одну строку без промежуточных аннотаций.</li><li>Нарушать порядок: фильтр по полю до его annotate.</li><li>Не проверять edge-cases с null-связями.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li>База: <code>qs = Model.objects.filter(...)</code></li><li>Аннотации: <code>qs = qs.annotate(...)</code></li><li>Фильтры: <code>qs = qs.filter(...)</code></li><li>Финал: <code>qs = qs.order_by(...)</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/topics/db/queries/" target="_blank">Making queries</a> + <a href="https://docs.djangoproject.com/en/stable/ref/models/expressions/" target="_blank">Query expressions</a>.</p>
""",
        'tasks': _tasks([
            ('Шаг 1. Базовый qs: удаленные исключить, company_id=1.', 'BleTag.objects.filter(deleted__isnull=True, company_id=1)', '', 'BleTag'),
            ('Шаг 2. Аннотируй route_id и route_title через F.', 'BleTag.objects.annotate(route_id=F("ble_route_id"), route_title=F("ble_route__title"))', '', 'BleTag'),
            ('Шаг 3. Аннотируй group_id на сегодня через Subquery(BleGroupRouteDate).', 'BleTag.objects.annotate(group_id=Subquery(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date()).order_by("-id").values("ble_group_id")[:1]))', '', 'BleTag'),
            ('Шаг 4. Аннотируй has_plan_today через Exists.', 'BleTag.objects.annotate(has_plan_today=Exists(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date())))', '', 'BleTag'),
            ('Шаг 5. Аннотируй has_inspection_today через Exists.', 'BleTag.objects.annotate(has_inspection_today=Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__date=timezone.now().date())))', '', 'BleTag'),
            ('Шаг 6. Аннотируй record_dt как max даты обхода.', 'BleTag.objects.annotate(record_dt=Subquery(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk")).values("ble_id").annotate(max_dt=Max("record_dt")).values("max_dt")[:1]))', '', 'BleTag'),
            ('Шаг 7. Аннотируй inspection_status простым Case: если has_plan_today=True и has_inspection_today=False -> False, иначе True.', 'BleTag.objects.annotate(has_plan_today=Exists(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date())), has_inspection_today=Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__date=timezone.now().date()))).annotate(inspection_status=Case(When(Q(has_plan_today=True) & Q(has_inspection_today=False), then=Value(False)), default=Value(True), output_field=BooleanField()))', '', 'BleTag'),
            ('Шаг 8. Примени map_only: status=installed_working.', 'BleTag.objects.filter(status=1)', '', 'BleTag'),
            ('Шаг 9. Примени route_filter=[1].', 'BleTag.objects.filter(ble_route_id__in=[1])', '', 'BleTag'),
            ('Шаг 10. Примени search_value="ble-00" по трём полям через OR.', 'BleTag.objects.filter(Q(ble_number__icontains="ble-00") | Q(mac_address__icontains="ble-00") | Q(chip_uuid__icontains="ble-00"))', '', 'BleTag'),
        ], 'BleTag'),
    },
    {
        'slug': 'final-practice',
        'name': 'Итоговая практика: смешанные задачи',
        'order': 16,
        'theory': """
<h4>Что это</h4>
<p>Итоговая практика на смешанные техники ORM. Здесь важно не только «написать запрос», но и выбрать правильный инструмент под задачу.</p>
<h4>Как работает в SQL</h4>
<p>Комбинация условий, подзапросов, аннотаций и сортировок компилируется в единый SQL-конвейер.</p>
<h4>Типовые ошибки</h4>
<ul><li>Неочевидный порядок условий в <code>Case</code>.</li><li>Лишние подзапросы вместо Exists.</li><li>Слишком ранний <code>count()</code>/<code>list()</code> при построении запроса.</li></ul>
<h4>Мини-шпаргалка</h4>
<ul><li>Логика: <code>Q</code></li><li>Вычисления: <code>annotate + Case/When</code></li><li>Подзапросы: <code>Subquery/OuterRef/Exists</code></li><li>Оптимизация: <code>select_related/prefetch_related</code></li></ul>
<h4>Документация</h4>
<p><a href="https://docs.djangoproject.com/en/stable/" target="_blank">Django documentation</a> — основной ориентир по всем разделам ORM.</p>
""",
        'tasks': _tasks([
            ('Верни рабочие BLE с low charge, у которых есть маршрут на сегодня, но нет обхода сегодня.', 'BleTag.objects.annotate(has_plan_today=Exists(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date())), has_inspection_today=Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__date=timezone.now().date()))).filter(status=1, charge_value__lte=15, has_plan_today=True, has_inspection_today=False)', '', 'BleTag'),
            ('Верни BLE и аннотируй group_title на сегодня + last record dt.', 'BleTag.objects.annotate(group_title=Subquery(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("ble_route_id"), dt=timezone.now().date()).order_by("-id").values("ble_group__title")[:1]), record_dt=Subquery(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk")).values("ble_id").annotate(m=Max("record_dt")).values("m")[:1]))', '', 'BleTag'),
            ('Верни BLE со сложным фильтром: (status=1 и bypass_status=1) или (status=2 и charge<=20).', 'BleTag.objects.filter((Q(status=1) & Q(bypass_status=1)) | (Q(status=2) & Q(charge_value__lte=20)))', '', 'BleTag'),
            ('Верни площадки, где есть >=2 BLE метки (аннотация + фильтр).', 'ConstructionSite.objects.annotate(tag_count=Count("ble_tags")).filter(tag_count__gte=2)', '', 'ConstructionSite'),
            ('Верни маршруты, у которых есть группы на сегодня и минимум одна рабочая BLE-метка.', 'BleRoute.objects.annotate(has_group_today=Exists(BleGroupRouteDate.objects.filter(ble_route_id=OuterRef("pk"), dt=timezone.now().date())), working_count=Count("ble_tags", filter=Q(ble_tags__status=1))).filter(has_group_today=True, working_count__gt=0)', '', 'BleRoute'),
            ('Верни BLE без обходов за последние 2 дня.', 'BleTag.objects.filter(~Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__gte=timezone.now()-timedelta(days=2))))', '', 'BleTag'),
            ('Верни BLE, отсортированные по max record_dt по убыванию, затем id.', 'BleTag.objects.annotate(record_dt=Subquery(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk")).values("ble_id").annotate(m=Max("record_dt")).values("m")[:1])).order_by("-record_dt", "id")', '', 'BleTag'),
            ('Верни OrgObject с has_plan и has_ble_tags (оба через Exists).', 'OrgObject.objects.annotate(has_plan=Exists(TimesheetPlan.objects.filter(org_object_id=OuterRef("pk"))), has_ble_tags=Exists(BleTag.objects.filter(construction_site_id=OuterRef("construction_site_id"))))', '', 'OrgObject'),
            ('Верни BLE с inspection_status (простая версия) и отфильтруй inspection_status=True.', 'BleTag.objects.annotate(has_inspection_today=Exists(BleInspectionRecord.objects.filter(ble_id=OuterRef("pk"), record_dt__date=timezone.now().date()))).annotate(inspection_status=Case(When(has_inspection_today=True, then=Value(True)), default=Value(False), output_field=BooleanField())).filter(inspection_status=True)', '', 'BleTag'),
            ('Верни BLE с map_only + поиск "chip" + сортировка по charge_value desc.', 'BleTag.objects.filter(status=1).filter(Q(ble_number__icontains="chip") | Q(mac_address__icontains="chip") | Q(chip_uuid__icontains="chip")).order_by("-charge_value", "id")', '', 'BleTag'),
        ], 'BleTag'),
    },
]
