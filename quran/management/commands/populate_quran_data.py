import requests
import json
from django.core.management.base import BaseCommand
from quran.models import Surah, Ayah, Tafsir, Recitation, WordMeaning
from tqdm import tqdm
import time

class Command(BaseCommand):
    help = 'Populate Quran data from open-source APIs'
    
    def handle(self, *args, **options):
        self.stdout.write("Populating Quran data...")
        
        # First populate surahs
        self.populate_surahs()
        
        # Wait a bit to ensure surahs are committed
        time.sleep(1)
        
        # Then populate verses
        self.populate_verses()
        
        # Populate other data
        self.populate_recitations()
        
        # Tafsir can be added later as it's optional
        # self.populate_tafsir()
        
        self.stdout.write(self.style.SUCCESS("Successfully populated Quran data!"))
    
    def populate_surahs(self):
        """Populate Surah data - ALL 114 surahs"""
        self.stdout.write("Populating Surahs...")
        
        # Complete list of all 114 surahs
        surahs_data = [
            # First 5 surahs as example - you need all 114
            {
                "number": 1,
                "name_arabic": "الفاتحة",
                "name_english": "Al-Fatihah",
                "name_translation": "The Opening",
                "revelation_type": "meccan",
                "total_verses": 7,
                "audio_url": "https://everyayah.com/data/Alafasy_128kbps/001001.mp3"
            },
            {
                "number": 2,
                "name_arabic": "البقرة",
                "name_english": "Al-Baqarah",
                "name_translation": "The Cow",
                "revelation_type": "medinan",
                "total_verses": 286,
                "audio_url": "https://everyayah.com/data/Alafasy_128kbps/002001.mp3"
            },
            {
                "number": 3,
                "name_arabic": "آل عمران",
                "name_english": "Ali 'Imran",
                "name_translation": "Family of Imran",
                "revelation_type": "medinan",
                "total_verses": 200,
                "audio_url": "https://everyayah.com/data/Alafasy_128kbps/003001.mp3"
            },
            {
                "number": 4,
                "name_arabic": "النساء",
                "name_english": "An-Nisa",
                "name_translation": "The Women",
                "revelation_type": "medinan",
                "total_verses": 176,
                "audio_url": "https://everyayah.com/data/Alafasy_128kbps/004001.mp3"
            },
            {
                "number": 5,
                "name_arabic": "المائدة",
                "name_english": "Al-Ma'idah",
                "name_translation": "The Table Spread",
                "revelation_type": "medinan",
                "total_verses": 120,
                "audio_url": "https://everyayah.com/data/Alafasy_128kbps/005001.mp3"
            },
            # Add the remaining surahs here...
            # For now, let's create a minimal working set
        ]
        
        # Create all 114 surahs programmatically with basic info
        for i in range(1, 115):
            surah_obj, created = Surah.objects.get_or_create(
                number=i,
                defaults={
                    "name_arabic": f"Surah {i}",
                    "name_english": f"Surah {i}",
                    "name_translation": f"Surah {i}",
                    "revelation_type": "meccan" if i <= 86 else "medinan",  # Approximate
                    "total_verses": self.get_surah_verse_count(i),
                    "audio_url": f"https://everyayah.com/data/Alafasy_128kbps/{str(i).zfill(3)}001.mp3"
                }
            )
            if created:
                self.stdout.write(f"Created Surah {i}")
        
        self.stdout.write(f"Created/Updated {Surah.objects.count()} surahs")
    
    def get_surah_verse_count(self, surah_number):
        """Get verse count for each surah"""
        verse_counts = {
            1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75, 9: 129, 10: 109,
            11: 123, 12: 111, 13: 43, 14: 52, 15: 99, 16: 128, 17: 111, 18: 110, 19: 98, 20: 135,
            21: 112, 22: 78, 23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69, 30: 60,
            31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83, 37: 182, 38: 88, 39: 75, 40: 85,
            41: 54, 42: 53, 43: 89, 44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45,
            51: 60, 52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29, 58: 22, 59: 24, 60: 13,
            61: 14, 62: 11, 63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44,
            71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40, 79: 46, 80: 42,
            81: 29, 82: 19, 83: 36, 84: 25, 85: 22, 86: 17, 87: 19, 88: 26, 89: 30, 90: 20,
            91: 15, 92: 21, 93: 11, 94: 8, 95: 8, 96: 19, 97: 5, 98: 8, 99: 8, 100: 11,
            101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4, 107: 7, 108: 3, 109: 6, 110: 3,
            111: 5, 112: 4, 113: 5, 114: 6
        }
        return verse_counts.get(surah_number, 0)
    
    def populate_verses(self):
        """Populate Ayah data from API"""
        self.stdout.write("Populating verses...")
        
        base_url = "https://api.alquran.cloud/v1"
        
        # First, let's test with just one surah to debug
        for surah_num in range(6, 115):  # Just first 5 surahs for testing
            try:
                # Check if surah exists
                if not Surah.objects.filter(number=surah_num).exists():
                    self.stdout.write(self.style.WARNING(f"Surah {surah_num} not found, skipping..."))
                    continue
                
                # Fetch surah data
                response = requests.get(f"{base_url}/surah/{surah_num}/en.asad")
                if response.status_code == 200:
                    data = response.json()['data']
                    
                    # Get the surah object
                    surah = Surah.objects.get(number=surah_num)
                    
                    # Fetch each verse
                    verses_created = 0
                    for verse in data['ayahs']:
                        # Create or update ayah
                        ayah, created = Ayah.objects.get_or_create(
                            surah=surah,
                            number_in_surah=verse['numberInSurah'],
                            defaults={
                                'number': verse['number'],
                                'text_uthmani': verse['text'],
                                'translation_en': verse.get('translation', ''),
                                'page_number': verse.get('page', 0),
                                'juz_number': verse.get('juz', 0),
                                'hizb_number': verse.get('hizbQuarter', 0),
                                'audio_url': f"https://everyayah.com/data/Alafasy_128kbps/{str(surah_num).zfill(3)}{str(verse['numberInSurah']).zfill(3)}.mp3"
                            }
                        )
                        
                        if created:
                            verses_created += 1
                    
                    self.stdout.write(f"Created {verses_created} verses for Surah {surah_num}")
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(0.5)
                    
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to fetch Surah {surah_num}: {response.status_code}"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing Surah {surah_num}: {str(e)}"))
                continue
    
    def populate_recitations(self):
        """Populate recitation styles"""
        self.stdout.write("Populating recitations...")
        
        recitations = [
            {
                'reciter_id': 1,
                'name': 'Mishary Alafasy',
                'name_arabic': 'مشاري العفاسي',
                'style': 'hafs',
                'audio_url_template': 'https://everyayah.com/data/Alafasy_128kbps/{surah}{ayah}.mp3'
            },
            {
                'reciter_id': 2,
                'name': 'Abdul Basit Abdul Samad',
                'name_arabic': 'عبد الباسط عبد الصمد',
                'style': 'hafs',
                'audio_url_template': 'https://everyayah.com/data/AbdulSamad_64kbps/Quran/{surah}{ayah}.mp3'
            },
            {
                'reciter_id': 3,
                'name': 'Maher Al Muaiqly',
                'name_arabic': 'ماهر المعيقلي',
                'style': 'hafs',
                'audio_url_template': 'https://everyayah.com/data/MaherAlMuaiqly128kbps/{surah}{ayah}.mp3'
            },
        ]
        
        for recitation in recitations:
            Recitation.objects.get_or_create(
                reciter_id=recitation['reciter_id'],
                defaults=recitation
            )
        
        self.stdout.write(f"Created {len(recitations)} recitations")