# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from trainer.models import Topic, Task
from trainer.data.tasks_data import TOPICS


class Command(BaseCommand):
    help = 'Загружает темы и задания из trainer/data/tasks_data.py'

    def handle(self, *args, **options):
        Task.objects.all().delete()
        Topic.objects.all().delete()

        for t in TOPICS:
            tasks_data = t.get('tasks', [])
            topic = Topic.objects.create(
                slug=t['slug'],
                name=t['name'],
                order=t['order'],
                theory=t.get('theory', ''),
            )
            for task_data in tasks_data:
                Task.objects.create(
                    topic=topic,
                    order=task_data['order'],
                    theory=task_data.get('theory', ''),
                    problem=task_data['problem'],
                    solution_code=task_data['solution_code'],
                    hint_model=task_data.get('hint_model', ''),
                )
        self.stdout.write(self.style.SUCCESS(f'Загружено тем: {Topic.objects.count()}, заданий: {Task.objects.count()}'))
