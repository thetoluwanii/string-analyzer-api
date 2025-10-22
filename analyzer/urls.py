from django.urls import path
from . import views

urlpatterns = [
    path('strings/', views.StringListCreateAPIView.as_view()),
    path('strings/<str:value>/', views.StringDetailAPIView.as_view()),
    path('strings/filter-by-natural-language/', views.NLFilterAPIView.as_view()),
]
