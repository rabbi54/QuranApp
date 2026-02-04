from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
import re

class WordMeaningSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordMeaning
        fields = ['word_index', 'arabic_word', 'transliteration', 
                 'pronunciation_audio', 'meaning_en', 'root_word']

class AyahSerializer(serializers.ModelSerializer):
    surah_name = serializers.CharField(source='surah.name_english', read_only=True)
    words = WordMeaningSerializer(source='word_meanings', many=True, read_only=True)
    
    # Add EXTRA cleaned fields (original fields remain as-is)
    text_uthmani_cleaned = serializers.SerializerMethodField()
    words_arabic_cleaned = serializers.SerializerMethodField()
    
    class Meta:
        model = Ayah
        fields = ['id', 'surah', 'surah_name', 'number_in_surah', 
                 'text_uthmani', 'text_uthmani_cleaned',  # Original + Cleaned
                 'transliteration', 'translation_en', 'translation_bn',
                 'words_arabic', 'words_arabic_cleaned',  # Original + Cleaned
                 'words_transliteration', 'words_translation',
                 'audio_url', 'audio_segments', 'segment_timestamps',
                 'page_number', 'juz_number', 'words']
    
    def get_text_uthmani_cleaned(self, obj):
        """Return text with Bismillah automatically removed"""
        return self._clean_bismillah_from_text(obj.text_uthmani, obj)
    
    def get_words_arabic_cleaned(self, obj):
        """Return words with Bismillah automatically removed"""
        return self._clean_bismillah_from_words(obj.words_arabic or [], obj, 'arabic')
    
    def _clean_bismillah_from_text(self, text, obj):
        """Remove Bismillah from text if needed"""
        # Only clean for first ayah of surahs 2-114
        if obj.surah.number != 1 and obj.surah.number != 9 and obj.number_in_surah == 1:
            return self._clean_text(text)
        return text
    
    def _clean_bismillah_from_words(self, words, obj, word_type):
        """Remove Bismillah words if needed"""
        # Only clean for first ayah of surahs 2-114
        if obj.surah.number != 1 and obj.surah.number != 9 and obj.number_in_surah == 1:
            return self._clean_words(words, word_type)
        return words
    
    def _clean_text(self, text):
        """Actual text cleaning logic"""
        if not text:
            return text
        
        patterns = [
            'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
            'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ',
            'بِسْمِٱللَّهِٱلرَّحْمَٰنِٱلرَّحِيمِ',
        ]
        
        for pattern in patterns:
            if pattern in text:
                text = text.replace(pattern, '')
                break
        
        text = re.sub(r'^\s*[\.،,:;]\s*', '', text)
        return text.strip()
    
    def _clean_words(self, words, word_type):
        """Actual word cleaning logic"""
        if len(words) < 4:
            return words
        
        bismillah_arabic = ['بِسْمِ', 'اللَّهِ', 'الرَّحْمَٰنِ', 'الرَّحِيمِ']
        
        # Check if first 4 words match Bismillah
        is_bismillah = all(
            bismillah_arabic[i] in words[i] 
            for i in range(min(4, len(words)))
        )
        
        if is_bismillah:
            return words[4:]
        
        return words
    
class TafsirSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tafsir
        fields = ['source', 'text', 'language']

class SurahSerializer(serializers.ModelSerializer):
    class Meta:
        model = Surah
        fields = ['number', 'name_arabic', 'name_english', 'name_translation_bn',
                 'revelation_type', 'total_verses', 'audio_url']

class UserNoteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = UserNote
        fields = ['id', 'ayah', 'note', 'created_at', 'updated_at', 'user']
        read_only_fields = ['created_at', 'updated_at']

class BookmarkSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = Bookmark
        fields = ['id', 'ayah', 'bookmark_type', 'created_at', 'user']

class RecitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recitation
        fields = ['id', 'reciter_id', 'name', 'name_arabic', 'style', 'audio_url_template']


class BismillahSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bismillah
        fields = ['text_uthmani', 'text_simple', 'translation_en', 'audio_url', 'words']