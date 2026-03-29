from django.urls import path
from .views import cafe_list, cafe_detail
from . import views

urlpatterns = [
    path('', cafe_list, name='cafe_list'),
    path("cafe/<int:cafe_id>/", views.cafe_detail, name="cafe_detail"),
    path('cafe/<int:cafe_id>/reviews/', views.load_more_reviews, name='load_more_reviews'),
]