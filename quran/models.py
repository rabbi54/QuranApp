from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField  # If using PostgreSQL
import json

# For SQLite/MySQL alternative to ArrayField
class JSONField(models.TextField):
    """Custom JSON field for storing lists/dicts"""
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return json.loads(value)
    
    def to_python(self, value):
        if isinstance(value, str):
            return json.loads(value)
        return value
    
    def get_prep_value(self, value):
        return json.dumps(value)

class Surah(models.Model):
    """Model for Quran chapters"""
    number = models.PositiveIntegerField(primary_key=True)
    name_arabic = models.CharField(max_length=100)
    name_english = models.CharField(max_length=100)
    name_translation = models.CharField(max_length=100)
    name_translation_bn = models.CharField(max_length=100, blank=True)  # Bangla translation
    name_translation_ur = models.CharField(max_length=100, blank=True)  # Urdu translation
    revelation_type = models.CharField(max_length=20, choices=[
        ('meccan', 'Meccan'),
        ('medinan', 'Medinan')
    ])
    total_verses = models.PositiveIntegerField()
    
    # Audio file for the entire surah
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    
    class Meta:
        ordering = ['number']
    
    def __str__(self):
        return f"{self.number}. {self.name_english}"

class Ayah(models.Model):
    """Model for individual Quran verses"""
    surah = models.ForeignKey(Surah, on_delete=models.CASCADE, related_name='verses')
    number = models.PositiveIntegerField()
    number_in_surah = models.PositiveIntegerField()
    
    # Text fields
    text_uthmani = models.TextField()  # Uthmani script
    text_indopak = models.TextField(blank=True)  # Indopak script
    text_simple = models.TextField(blank=True)  # Simple Arabic
    
    # Transliteration
    transliteration = models.TextField(blank=True)
    
    # Translations
    translation_en = models.TextField(blank=True)
    translation_id = models.TextField(blank=True)  # Indonesian
    translation_ur = models.TextField(blank=True)  # Urdu
    translation_bn = models.TextField(blank=True)  # Bengali
    
    # Word by word breakdown
    words_arabic = JSONField(blank=True, default=list)  # List of Arabic words
    words_transliteration = JSONField(blank=True, default=list)  # List of transliterations
    words_translation = JSONField(blank=True, default=list)  # List of word meanings
    
    # Audio
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    audio_segments = JSONField(blank=True, default=list)  # Audio segments for each word
    segment_timestamps = JSONField(blank=True, default=list)  # Start times for each word
    
    # Position data for highlighting
    page_number = models.PositiveIntegerField()
    juz_number = models.PositiveIntegerField()
    hizb_number = models.PositiveIntegerField()
    rub_number = models.PositiveIntegerField(blank=True, null=True)
    
    # Sajdah ayah
    sajdah = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['surah__number', 'number_in_surah']
        unique_together = ['surah', 'number_in_surah']
    
    def __str__(self):
        return f"{self.surah.number}:{self.number_in_surah}"

class Tafsir(models.Model):
    """Model for verse explanations/tafsir"""
    ayah = models.ForeignKey(Ayah, on_delete=models.CASCADE, related_name='tafsirs')
    source = models.CharField(max_length=100, choices=[
        ('ibn_kathir', 'Tafsir Ibn Kathir'),
        ('jalalayn', 'Tafsir al-Jalalayn'),
        ('qurtubi', 'Tafsir al-Qurtubi'),
        ('tabari', 'Tafsir al-Tabari'),
        ('modern', 'Modern Tafsir'),
    ])
    text = models.TextField()
    language = models.CharField(max_length=10, default='en')
    
    class Meta:
        unique_together = ['ayah', 'source', 'language']
    
    def __str__(self):
        return f"{self.ayah} - {self.get_source_display()}"

class UserNote(models.Model):
    """Model for user personal notes on verses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quran_notes')
    ayah = models.ForeignKey(Ayah, on_delete=models.CASCADE, related_name='user_notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'ayah']
    
    def __str__(self):
        return f"{self.user.username} - {self.ayah}"

class Bookmark(models.Model):
    """Model for user bookmarks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quran_bookmarks')
    ayah = models.ForeignKey(Ayah, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Bookmark type/color
    bookmark_type = models.CharField(max_length=20, default='default', choices=[
        ('default', 'Default'),
        ('favorite', 'Favorite'),
        ('memorized', 'Memorized'),
        ('study', 'Study'),
    ])
    
    class Meta:
        unique_together = ['user', 'ayah']
    
    def __str__(self):
        return f"{self.user.username} - {self.ayah}"

class WordMeaning(models.Model):
    """Detailed meaning and pronunciation for individual words"""
    ayah = models.ForeignKey(Ayah, on_delete=models.CASCADE, related_name='word_meanings')
    word_index = models.PositiveIntegerField()  # Position in verse
    arabic_word = models.CharField(max_length=100)
    transliteration = models.CharField(max_length=200)
    pronunciation_audio = models.URLField(max_length=500, blank=True, null=True)
    
    # Meanings in different languages
    meaning_en = models.TextField()
    meaning_id = models.TextField(blank=True)
    meaning_ur = models.TextField(blank=True)
    
    # Linguistic information
    root_word = models.CharField(max_length=50, blank=True)
    part_of_speech = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['ayah', 'word_index']
        unique_together = ['ayah', 'word_index']
    
    def __str__(self):
        return f"{self.arabic_word} - {self.meaning_en[:50]}"

class Recitation(models.Model):
    """Different Quran recitations/audio styles"""
    reciter_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    name_arabic = models.CharField(max_length=100, blank=True)
    style = models.CharField(max_length=50, choices=[
        ('hafs', 'Hafs'),
        ('warsh', 'Warsh'),
        ('qaloon', 'Qaloon'),
        ('duri', 'Al-Duri'),
    ])
    audio_url_template = models.URLField(max_length=500)  # Template with {surah} and {ayah} placeholders
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_style_display()})"
    


# Add this model
class Bismillah(models.Model):
    text_uthmani = models.TextField(default='بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
    translation_en = models.TextField(default='In the name of Allah, the Entirely Merciful, the Especially Merciful.')
    audio_url = models.URLField(default='https://everyayah.com/data/Alafasy_128kbps/001001.mp3')
    words = models.JSONField(default=list)
    
    @classmethod
    def get_default(cls):
        bismillah, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'words': [
                    {"index": 1, "arabic": "بِسْمِ", "audio": "https://words.audios.quranwbw.com/001/001_001_001.mp3"},
                    {"index": 2, "arabic": "اللَّهِ", "audio": "https://words.audios.quranwbw.com/001/001_001_002.mp3"},
                    {"index": 3, "arabic": "الرَّحْمَٰنِ", "audio": "https://words.audios.quranwbw.com/001/001_001_003.mp3"},
                    {"index": 4, "arabic": "الرَّحِيمِ", "audio": "https://words.audios.quranwbw.com/001/001_001_004.mp3"}
                ]
            }
        )
        return bismillah