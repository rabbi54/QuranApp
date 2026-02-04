from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework.pagination import PageNumberPagination
from .models import *
from .serializers import *
import json

# Custom pagination
class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# Template Views
def home(request):
    """Home page view"""
    context = {
        'total_surahs': Surah.objects.count(),
        'total_verses': Ayah.objects.count(),
        'total_recitations': Recitation.objects.count(),
    }
    return render(request, 'home.html', context)

@login_required
def quran_reader(request):
    """Quran reader page"""
    surahs = Surah.objects.all()
    return render(request, 'quran/reader.html', {'surahs': surahs})

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now login.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# API Views
class SurahViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Surah.objects.all()
    serializer_class = SurahSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['get'])
    def verses(self, request, pk=None):
        surah = self.get_object()
        verses = Ayah.objects.filter(surah=surah)
        serializer = AyahSerializer(verses, many=True)
        return Response(serializer.data)

class AyahViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AyahSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        queryset = Ayah.objects.all().select_related('surah')
        
        surah = self.request.query_params.get('surah', None)
        if surah:
            queryset = queryset.filter(surah__number=surah)
        
        page = self.request.query_params.get('page', None)
        if page:
            queryset = queryset.filter(page_number=page)
        
        juz = self.request.query_params.get('juz', None)
        if juz:
            queryset = queryset.filter(juz_number=juz)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def tafsir(self, request, pk=None):
        ayah = self.get_object()
        tafsirs = Tafsir.objects.filter(ayah=ayah)
        serializer = TafsirSerializer(tafsirs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def audio(self, request, pk=None):
        ayah = self.get_object()
        recitation_id = request.query_params.get('recitation', 1)
        
        try:
            recitation = Recitation.objects.get(reciter_id=recitation_id)
            audio_url = recitation.audio_url_template.format(
                surah=str(ayah.surah.number).zfill(3),
                ayah=str(ayah.number_in_surah).zfill(3)
            )
        except:
            audio_url = ayah.audio_url or f"https://everyayah.com/data/Alafasy_128kbps/{str(ayah.surah.number).zfill(3)}{str(ayah.number_in_surah).zfill(3)}.mp3"
        
        return Response({
            'audio_url': audio_url, 
            'ayah': f"{ayah.surah.number}:{ayah.number_in_surah}",
            'surah_name': ayah.surah.name_english,
            'surah_name_translation_bn': ayah.surah.name_translation_bn,
            'ayah_number': ayah.number_in_surah
        })

class UserNoteViewSet(viewsets.ModelViewSet):
    serializer_class = UserNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserNote.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RecitationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recitation.objects.all()
    serializer_class = RecitationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class WordDetailView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def retrieve(self, request, ayah_id=None, word_index=None):
        try:
            word = WordMeaning.objects.get(ayah_id=ayah_id, word_index=word_index)
            return Response({
                'arabic': word.arabic_word,
                'transliteration': word.transliteration,
                'meaning': word.meaning_en,
                'pronunciation_audio': word.pronunciation_audio,
                'root': word.root_word,
            })
        except WordMeaning.DoesNotExist:
            try:
                ayah = Ayah.objects.get(id=ayah_id)
                words = ayah.text_uthmani.split()
                if word_index < len(words):
                    return Response({
                        'arabic': words[word_index],
                        'transliteration': f"word_{word_index + 1}",
                        'meaning': 'Meaning not available',
                        'pronunciation_audio': '',
                        'root': 'N/A',
                    })
            except:
                pass
            
            return Response({'error': 'Word not found'}, status=404)

# Simple API Views for frontend
@api_view(['GET'])
def get_surahs(request):
    """Simple API endpoint to get all surahs"""
    surahs = Surah.objects.all().order_by('number')
    serializer = SurahSerializer(surahs, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_surah_detail(request, surah_number):
    """Get single surah with verses"""
    try:
        surah = Surah.objects.get(number=surah_number)
        verses = Ayah.objects.filter(surah=surah).order_by('number_in_surah')
        
        surah_serializer = SurahSerializer(surah)
        verses_serializer = AyahSerializer(verses, many=True)
        
        return Response({
            'surah': surah_serializer.data,
            'verses': verses_serializer.data
        })
    except Surah.DoesNotExist:
        return Response({'error': 'Surah not found'}, status=404)

@api_view(['GET'])
def get_verses(request):
    """Get verses with filtering"""
    surah = request.GET.get('surah')
    page = request.GET.get('page')
    
    queryset = Ayah.objects.all()
    
    if surah:
        queryset = queryset.filter(surah__number=surah)
    
    if page:
        queryset = queryset.filter(page_number=page)
    
    queryset = queryset.order_by('surah__number', 'number_in_surah')
    
    serializer = AyahSerializer(queryset, many=True)
    return Response(serializer.data)

# Direct API endpoints for frontend compatibility
@api_view(['GET'])
def ayah_audio_direct(request, ayah_id):
    """Direct audio endpoint for frontend compatibility"""
    try:
        ayah = Ayah.objects.get(id=ayah_id)
        recitation_id = request.GET.get('recitation', 1)
        
        try:
            recitation = Recitation.objects.get(reciter_id=recitation_id)
            audio_url = recitation.audio_url_template.format(
                surah=str(ayah.surah.number).zfill(3),
                ayah=str(ayah.number_in_surah).zfill(3)
            )
        except:
            audio_url = ayah.audio_url or f"https://everyayah.com/data/Alafasy_128kbps/{str(ayah.surah.number).zfill(3)}{str(ayah.number_in_surah).zfill(3)}.mp3"
        
        return Response({
            'audio_url': audio_url, 
            'ayah': f"{ayah.surah.number}:{ayah.number_in_surah}",
            'surah_name': ayah.surah.name_english,
            'surah_name_translation_bn': ayah.surah.name_translation_bn,
            'ayah_number': ayah.number_in_surah,
            'arabic_text': ayah.text_uthmani
        })
    except Ayah.DoesNotExist:
        return Response({'error': 'Ayah not found'}, status=404)
    


# views.py - ADD ONLY THIS
class BismillahView(APIView):
    def get(self, request):
        bismillah = Bismillah.get_default()
        return Response({
            'text_uthmani': bismillah.text_uthmani,
            'translation_en': bismillah.translation_en,
            'audio_url': bismillah.audio_url,
            'words': bismillah.words
        })