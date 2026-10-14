# -*- coding: utf-8 -*-
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from trainer.models import (
    Topic,
    Task,
    Book,
    Author,
    Publisher,
    Category,
    Profile,
    Review,
    Shelf,
    Company,
    ConstructionSite,
    OrgObject,
    BleRoute,
    BleGroup,
    BleGroupRouteDate,
    BleTag,
    BleInspectionRecord,
    TimesheetPlan,
    InspectionGap,
)
from trainer.checker import check_answer, compile_solution_sql, compile_user_code_sql
import json


MODEL_MAP = {
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
    'BleRoute': BleRoute,
    'BleGroup': BleGroup,
    'BleGroupRouteDate': BleGroupRouteDate,
    'BleTag': BleTag,
    'BleInspectionRecord': BleInspectionRecord,
    'TimesheetPlan': TimesheetPlan,
    'InspectionGap': InspectionGap,
}


def _model_fields(model_name: str) -> list[str]:
    model = MODEL_MAP.get(model_name)
    if not model:
        return []
    fields = []
    for f in model._meta.get_fields():
        # Берём только реально полезные для заданий имена полей/связей
        if getattr(f, 'auto_created', False) and not getattr(f, 'concrete', False):
            continue
        fields.append(f.name)
    return sorted(set(fields))


def index(request):
    """Главная страница — единый фронт с сайдбаром и областью задания."""
    return render(request, 'trainer/index.html')


@require_http_methods(['GET'])
def api_topics(request):
    """Список тем для сайдбара."""
    topics = Topic.objects.order_by('order').values('id', 'slug', 'name', 'order')
    return JsonResponse({'topics': list(topics)})


@require_http_methods(['GET'])
def api_topic_detail(request, topic_id):
    """Тема с теорией и списком заданий (id, order, problem)."""
    try:
        topic = Topic.objects.get(pk=topic_id)
    except Topic.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    tasks = topic.tasks.order_by('order').values('id', 'order', 'problem')
    return JsonResponse({
        'id': topic.id,
        'slug': topic.slug,
        'name': topic.name,
        'theory': topic.theory,
        'tasks': list(tasks),
    })


@require_http_methods(['GET'])
def api_task_detail(request, task_id):
    """Одно задание: теория (перед заданием), формулировка, подсказка по модели."""
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse({
        'id': task.id,
        'topic_id': task.topic_id,
        'order': task.order,
        'theory': task.theory or '',
        'problem': task.problem,
        'hint_model': task.hint_model or '',
        'hint_model_fields': _model_fields(task.hint_model or ''),
        'solution_sql': compile_solution_sql(task.solution_code) or '',
    })


@require_http_methods(['POST'])
@csrf_exempt
def api_check(request):
    """Проверка кода пользователя. Body: {"task_id": int, "code": str}."""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        code = (data.get('code') or '').strip()
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'ok': False, 'message': 'Неверный запрос'}, status=400)
    if not task_id or not code:
        return JsonResponse({'ok': False, 'message': 'Укажите task_id и code'}, status=400)
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return JsonResponse({'ok': False, 'message': 'Задание не найдено'}, status=404)
    ok, message, sql = check_answer(code, task.solution_code)
    return JsonResponse({'ok': ok, 'message': message, 'sql': sql or ''})


@require_http_methods(['POST'])
@csrf_exempt
def api_sql(request):
    """Компиляция ORM-кода в SQL без проверки ответа. Body: {"code": str}."""
    try:
        data = json.loads(request.body)
        code = (data.get('code') or '').strip()
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'sql': '', 'error': 'Неверный запрос'}, status=400)
    if not code:
        return JsonResponse({'sql': '', 'error': 'Укажите code'}, status=400)
    sql, error = compile_user_code_sql(code)
    if error:
        return JsonResponse({'sql': '', 'error': error})
    return JsonResponse({'sql': sql or ''})
