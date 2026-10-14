# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('api/topics/', views.api_topics),
    path('api/topics/<int:topic_id>/', views.api_topic_detail),
    path('api/tasks/<int:task_id>/', views.api_task_detail),
    path('api/check/', views.api_check),
    path('api/sql/', views.api_sql),
]
