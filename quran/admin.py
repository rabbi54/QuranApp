from django.contrib import admin
from .models import *

@admin.register(Surah)
class SurahAdmin(admin.ModelAdmin):
    list_display = ['number', 'name_arabic', 'name_english', 'revelation_type', 'total_verses']
    search_fields = ['name_arabic', 'name_english']
    ordering = ['number']

@admin.register(Ayah)
class AyahAdmin(admin.ModelAdmin):
    list_display = ['surah', 'number_in_surah', 'page_number', 'juz_number']
    list_filter = ['surah', 'juz_number', 'page_number']
    search_fields = ['text_uthmani', 'translation_en']
    ordering = ['surah__number', 'number_in_surah']

@admin.register(Tafsir)
class TafsirAdmin(admin.ModelAdmin):
    list_display = ['ayah', 'source', 'language']
    list_filter = ['source', 'language']
    search_fields = ['text']

@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'ayah', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['note']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'ayah', 'bookmark_type', 'created_at']
    list_filter = ['user', 'bookmark_type']

@admin.register(WordMeaning)
class WordMeaningAdmin(admin.ModelAdmin):
    list_display = ['ayah', 'word_index', 'arabic_word', 'root_word']
    list_filter = ['ayah__surah']

@admin.register(Recitation)
class RecitationAdmin(admin.ModelAdmin):
    list_display = ['name', 'style', 'reciter_id']