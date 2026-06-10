# -*- coding: utf-8 -*-
"""
Проверка пользовательского кода: выполнение в ограниченном контексте и сравнение
результата с эталонным QuerySet (по списку pk с учётом порядка).
"""
import builtins
import ast
import re
from datetime import timedelta, date, datetime, time
from django.core.exceptions import FieldError
from django.db import DatabaseError
from django.db.models import QuerySet
from django.db.models import Q, F
from django.db.models import Count, Sum, Avg, Min, Max
from django.db.models import (
    OuterRef,
    Subquery,
    Exists,
    Case,
    When,
    Value,
    IntegerField,
    BooleanField,
    CharField,
    DecimalField,
    DateField,
    DateTimeField,
)
from django.db.models.functions import Coalesce as DjangoCoalesce
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


def Coalesce(*expressions, **extra):
    """
    Обёртка над Django Coalesce для учебного кейса:
    Coalesce(F("price"), Value(0)) при DecimalField price.
    На новых версиях Django такое выражение может падать из-за mixed types.
    """
    if 'output_field' not in extra:
        has_decimal = any(
            isinstance(getattr(expr, 'output_field', None), DecimalField)
            for expr in expressions
        )
        has_price_f = any(
            isinstance(expr, F) and getattr(expr, 'name', None) == 'price'
            for expr in expressions
        )
        has_plain_int_value = any(
            isinstance(expr, Value)
            and isinstance(getattr(expr, 'value', None), int)
            and not isinstance(getattr(expr, 'value', None), bool)
            for expr in expressions
        )
        if (has_decimal or has_price_f) and has_plain_int_value:
            extra['output_field'] = DecimalField(max_digits=10, decimal_places=2)
    return DjangoCoalesce(*expressions, **extra)


# Разрешённые объекты в контексте выполнения кода пользователя
ALLOWED = {
    'Book': Book,
    'Author': Author,
    'Publisher': Publisher,
    'Category': Category,
    'Profile': Profile,
    'Review': Review,
    'Shelf': Shelf,
    'Company': Company,
    'ConstructionSite': ConstructionSite,
    'OrgObject': OrgObject,
    'TimesheetPlan': TimesheetPlan,
    'InspectionGap': InspectionGap,
    'BleRoute': BleRoute,
    'BleGroup': BleGroup,
    'BleGroupRouteDate': BleGroupRouteDate,
    'BleTag': BleTag,
    'BleInspectionRecord': BleInspectionRecord,
    'Q': Q,
    'F': F,
    'Count': Count,
    'Sum': Sum,
    'Avg': Avg,
    'Min': Min,
    'Max': Max,
    'OuterRef': OuterRef,
    'Subquery': Subquery,
    'Exists': Exists,
    'Case': Case,
    'When': When,
    'Value': Value,
    'IntegerField': IntegerField,
    'BooleanField': BooleanField,
    'CharField': CharField,
    'DateField': DateField,
    'DateTimeField': DateTimeField,
    'Coalesce': Coalesce,
    'timezone': timezone,
    'timedelta': timedelta,
    'date': date,
    'datetime': datetime,
    'time': time,
}


def _get_annotation_keys(qs: QuerySet) -> list[str]:
    """Имена аннотаций, которые есть в QuerySet."""
    # query.annotations включает и alias'ы annotate
    return list(getattr(qs.query, 'annotations', {}).keys())


def _get_signature(qs: QuerySet, annotation_keys: list[str]) -> list:
    """
    Подпись результата: для обычного QuerySet — pk (+ аннотации);
    для values().annotate() — колонки из values() + аннотации (порядок как в запросе).
    """
    vs = getattr(qs.query, 'values_select', None)
    if vs:
        cols = list(vs)
        if annotation_keys:
            cols = cols + list(annotation_keys)
        return list(qs.values_list(*cols))
    if annotation_keys:
        return list(qs.values_list('pk', *annotation_keys))
    return list(qs.values_list('pk', flat=True))


def _database_check_hint(exc: Exception) -> str:
    """Подсказка по типичным ошибкам БД при проверке ORM."""
    msg = str(exc)
    if 'sub-select returns' in msg and 'expected 1' in msg:
        return (
            ' В Subquery(...) внутренний QuerySet должен выбирать одну колонку. '
            'После .annotate(max_insp=Max("record_dt")) обязательно сузь выборку: '
            '.values("max_insp")[:1] или полная цепочка '
            '.values("ble_id").annotate(max_insp=Max("record_dt")).values("max_insp")[:1].'
        )
    return ''


def _subquery_output_field_hint(exc: FieldError) -> str:
    msg = str(exc)
    if 'unknown output_field' in msg or 'Cannot resolve expression type' in msg:
        return (
            ' Частая причина: внутри Subquery(...) нужен QuerySet с ровно одной колонкой — '
            'например .values("record_dt")[:1] или .values("ble_id").annotate(...).values("max_dt")[:1]. '
            'Передавать «целую» модель без .values() нельзя: у выражения не будет output_field.'
        )
    return ''


def _timezone_mismatch_hint(user_code: str, solution_code: str) -> str:
    """Если эталон на timezone, а у пользователя datetime — поясняем разницу."""
    if 'datetime.now()' in user_code and 'timezone.now()' in solution_code:
        return (
            ' Подсказка: для «сегодня» в эталоне используется timezone.now().date(), '
            'где timezone — это django.utils.timezone (в тренажёре уже доступен). '
            'datetime.now() даёт наивное локальное время и может не совпасть с проверкой при USE_TZ.'
        )
    return ''


def check_answer(user_code: str, solution_code: str) -> tuple[bool, str]:
    """
    Выполняет solution_code и user_code, сравнивает результат с эталонным QuerySet
    (pk, либо values()+annotate, либо annotate на строках модели).
    """
    try:
        expected_qs = eval(solution_code, _safe_builtins(), ALLOWED)
    except Exception as e:
        return False, f'Ошибка в эталонном решении: {e}'

    if not isinstance(expected_qs, QuerySet):
        return False, 'Эталонное решение должно возвращать QuerySet.'

    annotation_keys = _get_annotation_keys(expected_qs)
    values_select = getattr(expected_qs.query, 'values_select', None)
    group_by_values = bool(values_select)

    normalized_user_code = _normalize_value_task_compat(user_code)

    try:
        user_qs = _eval_user_code(normalized_user_code)
    except DatabaseError as e:
        return False, f'Ошибка SQL при проверке: {e}.{_database_check_hint(e)}'
    except Exception as e:
        msg = f'Ошибка при выполнении кода: {e}'
        msg += _timezone_mismatch_hint(normalized_user_code, solution_code)
        return False, msg

    if not isinstance(user_qs, QuerySet):
        return False, 'Код должен возвращать QuerySet (например Model.objects.filter(...)).'

    if annotation_keys:
        user_ann = getattr(user_qs.query, 'annotations', {})
        for k in annotation_keys:
            if k not in user_ann:
                return False, (
                    f'В решении нет ожидаемой аннотации «{k}». '
                    f'Проверь имя в annotate(...=...) и что последняя строка возвращает этот QuerySet.'
                )
        if group_by_values:
            exp_vs = tuple(values_select)
            user_vs = getattr(user_qs.query, 'values_select', None)
            user_vs_t = tuple(user_vs) if user_vs else ()
            if exp_vs != user_vs_t:
                return False, (
                    'Набор и порядок полей в values(...) должны совпасть с эталоном '
                    f'(ожидалось {list(exp_vs)}, получено {list(user_vs_t) if user_vs_t else "без values"}).'
                )
        try:
            expected_signature = _get_signature(expected_qs, annotation_keys)
            user_signature = _get_signature(user_qs, annotation_keys)
        except FieldError as e:
            return False, (
                f'Аннотации объявлены, но запрос нельзя выполнить: {e}.'
                + _subquery_output_field_hint(e)
            )
        except DatabaseError as e:
            return False, f'Ошибка SQL при сравнении аннотаций: {e}.{_database_check_hint(e)}'

        if user_signature == expected_signature:
            return True, 'Верно!'

        if group_by_values:
            desc = f"{', '.join(values_select)}, {', '.join(annotation_keys)}"
        else:
            desc = f"pk, {', '.join(annotation_keys)}"
        return (
            False,
            f'Неверный результат/аннотации. Проверяются поля: {desc}. '
            f'Ожидалось: {expected_signature[:10]}{"..." if len(expected_signature) > 10 else ""}, '
            f'получено: {user_signature[:10]}{"..." if len(user_signature) > 10 else ""}'
            + _timezone_mismatch_hint(normalized_user_code, solution_code)
        )

    try:
        expected_signature = _get_signature(expected_qs, [])
        user_signature = _get_signature(user_qs, [])
    except DatabaseError as e:
        return False, f'Ошибка SQL при проверке: {e}.{_database_check_hint(e)}'

    if user_signature == expected_signature:
        return True, 'Верно!'

    return (
        False,
        f'Неверный результат. Ожидалось: {expected_signature[:20]}{"..." if len(expected_signature) > 20 else ""}, '
        f'получено: {user_signature[:20]}{"..." if len(user_signature) > 20 else ""}'
        + _timezone_mismatch_hint(normalized_user_code, solution_code)
    )


def _normalize_value_task_compat(code: str) -> str:
    """
    Совместимость для учебной задачи Value/safe_price:
    разрешаем краткую запись annotate(Coalesce(F('price'), Value(0)))
    и приводим её к именованной аннотации safe_price.
    """
    pattern = (
        r"Book\.objects\.annotate\(\s*"
        r"Coalesce\(\s*F\((['\"])price\1\)\s*,\s*Value\(0\)\s*\)\s*"
        r"\)"
    )
    if re.fullmatch(pattern, (code or '').strip()):
        return 'Book.objects.annotate(safe_price=Coalesce(F("price"), Value(0)))'
    return code


def _safe_builtins():
    """Минимальный набор builtins без open, exec, __import__ и т.д."""
    safe = {}
    for name in ('None', 'True', 'False', 'abs', 'min', 'max', 'sum', 'len', 'range',
                 'tuple', 'list', 'dict', 'set', 'str', 'int', 'float', 'sorted'):
        if hasattr(builtins, name):
            safe[name] = getattr(builtins, name)
    return safe


def _eval_user_code(code: str):
    """
    Поддерживает:
    1) одно выражение (как раньше),
    2) многострочный код с присваиваниями, где последняя строка — выражение QuerySet.
    """
    source = (code or '').strip()
    if not source:
        raise ValueError('Пустой код.')

    # Быстрый путь: одно выражение
    try:
        compiled_expr = compile(source, '<string>', 'eval')
        return eval(compiled_expr, _safe_builtins(), dict(ALLOWED))
    except SyntaxError:
        pass

    # Многострочный путь: выполняем все statements, последнюю Expr — через eval
    tree = ast.parse(source, mode='exec')
    if not tree.body:
        raise ValueError('Пустой код.')

    globals_map = _safe_builtins()
    locals_map = dict(ALLOWED)

    last = tree.body[-1]
    if isinstance(last, ast.Expr):
        prelude = ast.Module(body=tree.body[:-1], type_ignores=[])
        prelude_code = compile(prelude, '<string>', 'exec')
        exec(prelude_code, globals_map, locals_map)
        expr_code = compile(ast.Expression(last.value), '<string>', 'eval')
        return eval(expr_code, globals_map, locals_map)

    full_code = compile(tree, '<string>', 'exec')
    exec(full_code, globals_map, locals_map)
    if 'result' in locals_map:
        return locals_map['result']
    raise ValueError('Последней строкой должно быть выражение QuerySet или задай переменную result.')
