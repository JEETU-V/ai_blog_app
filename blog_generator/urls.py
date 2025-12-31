from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('generate_blog/', views.generate_blog, name='generate_blog'),
    path('blogs/', views.blog_list, name='blog_list'),
    path('blog/<int:pk>/', views.blog_details, name='blog_details'),
    path('api/recent-blogs/', views.recent_blogs_api, name='recent_blogs_api'),
    path('api/user-stats/', views.user_stats_api, name='user_stats_api'),
]