from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'surahs', views.SurahViewSet)
router.register(r'verses', views.AyahViewSet, basename='ayah')
router.register(r'notes', views.UserNoteViewSet, basename='note')
router.register(r'bookmarks', views.BookmarkViewSet, basename='bookmark')
router.register(r'recitations', views.RecitationViewSet)

urlpatterns = [
    # Template views
    path('', views.home, name='home'),
    path('reader/', views.quran_reader, name='quran-reader'),
    path('register/', views.register, name='register'),
    path('surahs/', views.quran_reader, name='surah-list'),
    
    # Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Simple API endpoints for frontend
    # path('api/surahs/', views.get_surahs, name='api-surahs'),
    path('api/surahs/<int:surah_number>/', views.get_surah_detail, name='api-surah-detail'),
    # path('api/verses/', views.get_verses, name='api-verses'),
    
    # REST Framework API URLs
    path('api/', include(router.urls)),
    path('api/bismillah/', views.BismillahView.as_view(), name='bismillah'),

    # path('api/verse/<int:ayah_id>/word/<int:word_index>/', 
    #      views.WordDetailView.as_view({'get': 'retrieve'}), 
    #      name='word-detail'),
    # path('api/verse/<int:ayah_id>/audio/', 
    #      views.AyahViewSet.as_view({'get': 'audio'}), 
    #      name='ayah-audio'),
]