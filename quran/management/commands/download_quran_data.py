import requests
import json
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm
from quran.models import Surah, Ayah, Recitation, WordMeaning
import arabic_reshaper
from bidi.algorithm import get_display

class Command(BaseCommand):
    help = 'Download complete Quran data from open-source APIs'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Quran data download..."))
        
        with transaction.atomic():
            # Clear existing data
            self.stdout.write("Clearing existing data...")
            WordMeaning.objects.all().delete()
            Ayah.objects.all().delete()
            Surah.objects.all().delete()
            Recitation.objects.all().delete()
            
            # Download surahs
            self.download_surahs()
            
            # Download verses
            self.download_verses()
            
            # Download recitations
            self.download_recitations()
            
            # Create word meanings (sample for first surah)
            # self.create_word_meanings()
        
        self.stdout.write(self.style.SUCCESS("✅ Quran data download completed!"))
        self.stdout.write(f"📖 Surahs: {Surah.objects.count()}")
        self.stdout.write(f"🕌 Ayahs: {Ayah.objects.count()}")
        self.stdout.write(f"🎵 Recitations: {Recitation.objects.count()}")
    
    def download_surahs(self):
        """Download all 114 surahs from Al-Quran Cloud API"""
        self.stdout.write("Downloading Surahs...")
        
        url = "https://api.alquran.cloud/v1/surah"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            surahs = data['data']
            
            for surah_data in tqdm(surahs, desc="Creating Surahs"):
                Surah.objects.create(
                    number=surah_data['number'],
                    name_arabic=surah_data['name'],
                    name_english=surah_data['englishName'],
                    name_translation=surah_data['englishNameTranslation'],
                    revelation_type=surah_data['revelationType'].lower(),
                    total_verses=surah_data['numberOfAyahs'],
                    audio_url=f"https://everyayah.com/data/Alafasy_128kbps/{str(surah_data['number']).zfill(3)}001.mp3"
                )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {len(surahs)} Surahs"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading surahs: {e}"))
            # Create basic surahs as fallback
            self.create_basic_surahs()
    
    def create_basic_surahs(self):
        """Create basic surahs if API fails"""
        surahs_data = [
            (1, "الفاتحة", "Al-Fatihah", "The Opening", "meccan", 7),
            (2, "البقرة", "Al-Baqarah", "The Cow", "medinan", 286),
            (3, "آل عمران", "Ali 'Imran", "Family of Imran", "medinan", 200),
            (4, "النساء", "An-Nisa", "The Women", "medinan", 176),
            (5, "المائدة", "Al-Ma'idah", "The Table Spread", "medinan", 120),
            (6, "الأنعام", "Al-An'am", "The Cattle", "meccan", 165),
            (7, "الأعراف", "Al-A'raf", "The Heights", "meccan", 206),
            (8, "الأنفال", "Al-Anfal", "The Spoils of War", "medinan", 75),
            (9, "التوبة", "At-Tawbah", "The Repentance", "medinan", 129),
            (10, "يونس", "Yunus", "Jonah", "meccan", 109),
        ]
        
        for number, arabic, english, translation, revelation, verses in surahs_data:
            Surah.objects.create(
                number=number,
                name_arabic=arabic,
                name_english=english,
                name_translation=translation,
                revelation_type=revelation,
                total_verses=verses,
                audio_url=f"https://everyayah.com/data/Alafasy_128kbps/{str(number).zfill(3)}001.mp3"
            )
        
        self.stdout.write(self.style.WARNING(f"Created {len(surahs_data)} basic surahs"))
    
    def download_verses(self):
        """Download verses for first 10 surahs (for testing)"""
        self.stdout.write("Downloading verses...")
        
        # We'll download first 3 surahs to test
        for surah_num in range(1, 115):
            try:
                self.stdout.write(f"Downloading verses for Surah {surah_num}...")
                self.download_surah_verses(surah_num)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error downloading Surah {surah_num}: {e}"))
                continue
    
    def download_surah_verses(self, surah_number):
        """Download all verses for a specific surah"""
        try:
            # Get Arabic text
            arabic_url = f"https://api.alquran.cloud/v1/surah/{surah_number}/ar.alafasy"
            response = requests.get(arabic_url, timeout=30)
            response.raise_for_status()
            arabic_data = response.json()
            
            # Get English translation
            english_url = f"https://api.alquran.cloud/v1/surah/{surah_number}/en.asad"
            response_en = requests.get(english_url, timeout=30)
            response_en.raise_for_status()
            english_data = response_en.json()
            
            surah = Surah.objects.get(number=surah_number)
            
            # Create ayahs
            for i in range(len(arabic_data['data']['ayahs'])):
                arabic_ayah = arabic_data['data']['ayahs'][i]
                english_ayah = english_data['data']['ayahs'][i]
                
                # Calculate page, juz, hizb (simplified)
                page_number = arabic_ayah.get('page', self.calculate_page(surah_number, arabic_ayah['numberInSurah']))
                juz_number = arabic_ayah.get('juz', self.calculate_juz(surah_number, arabic_ayah['numberInSurah']))
                hizb_number = arabic_ayah.get('hizbQuarter', self.calculate_hizb(surah_number, arabic_ayah['numberInSurah']))
                
                Ayah.objects.create(
                    surah=surah,
                    number=arabic_ayah['number'],
                    number_in_surah=arabic_ayah['numberInSurah'],
                    text_uthmani=arabic_ayah['text'],
                    text_simple=arabic_ayah['text'],  # Same for now
                    translation_en=english_ayah.get('text', ''),
                    page_number=page_number,
                    juz_number=juz_number,
                    hizb_number=hizb_number,
                    audio_url=f"https://everyayah.com/data/Alafasy_128kbps/{str(surah_number).zfill(3)}{str(arabic_ayah['numberInSurah']).zfill(3)}.mp3"
                )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {len(arabic_data['data']['ayahs'])} verses for Surah {surah_number}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading verses for Surah {surah_number}: {e}"))
            # Create sample verses as fallback
            self.create_sample_verses(surah_number)
    
    def create_sample_verses(self, surah_number):
        """Create sample verses if API fails"""
        surah = Surah.objects.get(number=surah_number)
        
        # Sample verses for Al-Fatihah
        if surah_number == 1:
            verses = [
                (1, "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", "In the name of Allah, the Entirely Merciful, the Especially Merciful.", 1, 1, 1),
                (2, "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ", "[All] praise is [due] to Allah, Lord of the worlds -", 1, 1, 1),
                (3, "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", "The Entirely Merciful, the Especially Merciful,", 1, 1, 1),
                (4, "مَٰلِكِ يَوْمِ ٱلدِّينِ", "Sovereign of the Day of Recompense.", 1, 1, 1),
                (5, "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ", "It is You we worship and You we ask for help.", 1, 1, 1),
                (6, "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ", "Guide us to the straight path -", 1, 1, 1),
                (7, "صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ", "The path of those upon whom You have bestowed favor, not of those who have evoked [Your] anger or of those who are astray.", 1, 1, 1),
            ]
        else:
            # Create at least one sample verse for other surahs
            verses = [
                (1, f"Sample verse for Surah {surah_number}", f"Sample translation for Surah {surah_number}", 1, 1, 1),
            ]
        
        for number_in_surah, arabic, translation, page, juz, hizb in verses:
            Ayah.objects.create(
                surah=surah,
                number=number_in_surah,
                number_in_surah=number_in_surah,
                text_uthmani=arabic,
                text_simple=arabic,
                translation_en=translation,
                page_number=page,
                juz_number=juz,
                hizb_number=hizb,
                audio_url=f"https://everyayah.com/data/Alafasy_128kbps/{str(surah_number).zfill(3)}{str(number_in_surah).zfill(3)}.mp3"
            )
        
        self.stdout.write(self.style.WARNING(f"Created {len(verses)} sample verses for Surah {surah_number}"))
    
    def download_recitations(self):
        """Create recitation entries"""
        self.stdout.write("Creating recitations...")
        
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
            {
                'reciter_id': 4,
                'name': 'Hani Ar-Rifai',
                'name_arabic': 'هاني الرفاعي',
                'style': 'hafs',
                'audio_url_template': 'https://everyayah.com/data/Hani_Rifai_192kbps/{surah}{ayah}.mp3'
            },
        ]
        
        for recitation in recitations:
            Recitation.objects.create(**recitation)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(recitations)} recitations"))
    
    def create_word_meanings(self):
        """Create comprehensive word-by-word data for Quran verses"""
        self.stdout.write("Creating word meanings...")
        
        try:
            # We'll process first 114 surahs for demonstration
            surahs_to_process = range(1, 115)
            
            for surah_num in tqdm(surahs_to_process, desc="Processing surahs"):
                try:
                    self.process_surah_word_meanings(surah_num)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error processing surah {surah_num}: {e}"))
                    continue
            
            self.stdout.write(self.style.SUCCESS(f"✅ Word meanings created for {len(surahs_to_process)} surahs"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating word meanings: {e}"))
            # Create sample word meanings for Al-Fatihah as fallback
            self.create_sample_word_meanings()

    def process_surah_word_meanings(self, surah_number):
        """Process word meanings for a specific surah"""
        
        # URL for QuranWBW (Quran Word by Word) API
        wbw_url = f"https://api.quranwbw.com/v1/surahs/{surah_number}/ayahs"
        
        try:
            response = requests.get(wbw_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.parse_wbw_data(surah_number, data)
            else:
                # Fallback to Tanzil API
                self.process_tanzil_word_data(surah_number)
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Failed to fetch WBW data for surah {surah_number}: {e}"))
            # Try alternative source
            self.process_alternative_word_data(surah_number)

    def parse_wbw_data(self, surah_number, wbw_data):
        """Parse Quran Word-by-Word API data"""
        
        surah = Surah.objects.get(number=surah_number)
        
        for ayah_data in wbw_data.get('ayahs', []):
            ayah_number = ayah_data.get('ayah_number')
            
            try:
                ayah = Ayah.objects.get(
                    surah=surah,
                    number_in_surah=ayah_number
                )
                
                words = ayah_data.get('words', [])
                
                for word_index, word_data in enumerate(words):
                    # Extract word information
                    arabic_word = word_data.get('text_uthmani', '')
                    transliteration = word_data.get('transliteration', {}).get('text', '')
                    meaning = word_data.get('translation', {}).get('text', '')
                    root = word_data.get('root', '')
                    part_of_speech = word_data.get('part_of_speech', '')
                    
                    # Get pronunciation audio if available
                    pronunciation_audio = ''
                    if word_data.get('audio'):
                        pronunciation_audio = word_data.get('audio', {}).get('url', '')
                    
                    # Create WordMeaning object
                    WordMeaning.objects.update_or_create(
                        ayah=ayah,
                        word_index=word_index,
                        defaults={
                            'arabic_word': arabic_word,
                            'transliteration': transliteration,
                            'meaning_en': meaning,
                            'root_word': root,
                            'part_of_speech': part_of_speech,
                            'pronunciation_audio': pronunciation_audio
                        }
                    )
                
                self.stdout.write(f"  Processed {len(words)} words for Ayah {ayah_number}")
                
            except Ayah.DoesNotExist:
                continue
            except Exception as e:
                self.stdout.write(f"  Error processing ayah {ayah_number}: {e}")

    def process_tanzil_word_data(self, surah_number):
        """Process word data from Tanzil API"""
        
        # Tanzil word-by-word API endpoint
        tanzil_url = f"https://api.quran.com/api/v4/quran/word_by_word/{surah_number}"
        
        try:
            response = requests.get(tanzil_url, timeout=30)
            if response.status_code != 200:
                return
            
            data = response.json()
            verses = data.get('verses', [])
            
            surah = Surah.objects.get(number=surah_number)
            
            for verse_data in verses:
                ayah_number = verse_data.get('verse_number')
                
                try:
                    ayah = Ayah.objects.get(
                        surah=surah,
                        number_in_surah=ayah_number
                    )
                    
                    words = verse_data.get('words', [])
                    
                    for word_index, word_data in enumerate(words):
                        arabic_word = word_data.get('text_uthmani', '')
                        transliteration = word_data.get('transliteration', {}).get('text', '')
                        
                        # Get meaning from translation
                        meaning = ''
                        if word_data.get('translations'):
                            meaning = word_data.get('translations', [{}])[0].get('text', '')
                        
                        # Get root word
                        root = word_data.get('root', '')
                        
                        # Get part of speech
                        part_of_speech = word_data.get('part_of_speech', '')
                        
                        # Create WordMeaning
                        WordMeaning.objects.update_or_create(
                            ayah=ayah,
                            word_index=word_index,
                            defaults={
                                'arabic_word': arabic_word,
                                'transliteration': transliteration,
                                'meaning_en': meaning,
                                'root_word': root,
                                'part_of_speech': part_of_speech,
                                'pronunciation_audio': ''
                            }
                        )
                    
                except Ayah.DoesNotExist:
                    continue
                    
        except Exception as e:
            self.stdout.write(f"Tanzil API failed for surah {surah_number}: {e}")

    def process_alternative_word_data(self, surah_number):
        """Process word data from alternative sources"""
        
        # Alternative: Use local database or fallback to calculated data
        surah = Surah.objects.get(number=surah_number)
        ayahs = Ayah.objects.filter(surah=surah)
        
        for ayah in ayahs:
            # Split Arabic text into words
            arabic_words = self.split_arabic_text(ayah.text_uthmani)
            
            for word_index, arabic_word in enumerate(arabic_words):
                # Generate transliteration (basic)
                transliteration = self.generate_transliteration(arabic_word)
                
                # Get meaning from dictionary (simplified)
                meaning = self.get_word_meaning(arabic_word)
                
                # Get root (simplified - would need proper Arabic morphology)
                root = self.extract_root(arabic_word)
                
                WordMeaning.objects.update_or_create(
                    ayah=ayah,
                    word_index=word_index,
                    defaults={
                        'arabic_word': arabic_word,
                        'transliteration': transliteration,
                        'meaning_en': meaning,
                        'root_word': root,
                        'part_of_speech': '',
                        'pronunciation_audio': ''
                    }
                )
        
        self.stdout.write(f"Created basic word meanings for Surah {surah_number}")

    def create_sample_word_meanings(self):
        """Create comprehensive sample word meanings for Al-Fatihah and Al-Baqarah"""
        self.stdout.write("Creating sample word meanings...")
        
        # Comprehensive word meanings for Surah Al-Fatihah (The Opening)
        fatihah_words = {
            1: [  # Ayah 1: بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ
                (0, "بِسْمِ", "bismi", "In (the) name", "ب س م", "Preposition"),
                (1, "ٱللَّهِ", "Allahi", "(of) Allah", "ا ل ه", "Proper Noun"),
                (2, "ٱلرَّحْمَٰنِ", "Ar-Rahman", "The Most Gracious", "ر ح م", "Proper Noun"),
                (3, "ٱلرَّحِيمِ", "Ar-Raheem", "The Most Merciful", "ر ح م", "Proper Noun"),
            ],
            2: [  # Ayah 2: ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ
                (0, "ٱلْحَمْدُ", "Alhamdu", "All praise", "ح م د", "Noun"),
                (1, "لِلَّهِ", "lillahi", "is (for) Allah", "ل ل ه", "Preposition"),
                (2, "رَبِّ", "Rabb", "(the) Lord", "ر ب ب", "Noun"),
                (3, "ٱلْعَٰلَمِينَ", "al-'aalameen", "(of) the worlds", "ع ل م", "Noun"),
            ],
            3: [  # Ayah 3: ٱلرَّحْمَٰنِ ٱلرَّحِيمِ
                (0, "ٱلرَّحْمَٰنِ", "Ar-Rahman", "The Most Gracious", "ر ح م", "Proper Noun"),
                (1, "ٱلرَّحِيمِ", "Ar-Raheem", "The Most Merciful", "ر ح م", "Proper Noun"),
            ],
            4: [  # Ayah 4: مَٰلِكِ يَوْمِ ٱلدِّينِ
                (0, "مَٰلِكِ", "Maaliki", "Master", "م ل ك", "Noun"),
                (1, "يَوْمِ", "Yawmi", "(of the) Day", "ي و م", "Noun"),
                (2, "ٱلدِّينِ", "id-Deen", "(of) Judgment", "د ي ن", "Noun"),
            ],
            5: [  # Ayah 5: إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ
                (0, "إِيَّاكَ", "Iyyaka", "You alone", "ا ي ي", "Pronoun"),
                (1, "نَعْبُدُ", "na'budu", "we worship", "ع ب د", "Verb"),
                (2, "وَإِيَّاكَ", "wa iyyaka", "and You alone", "ا ي ي", "Conjunction + Pronoun"),
                (3, "نَسْتَعِينُ", "nasta'een", "we ask for help", "ع و ن", "Verb"),
            ],
            6: [  # Ayah 6: ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ
                (0, "ٱهْدِنَا", "Ihdina", "Guide us", "ه د ي", "Verb"),
                (1, "ٱلصِّرَٰطَ", "as-Siraat", "(to) the path", "ص ر ط", "Noun"),
                (2, "ٱلْمُسْتَقِيمَ", "al-Mustaqeem", "straight", "ق و م", "Adjective"),
            ],
            7: [  # Ayah 7: صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ
                (0, "صِرَٰطَ", "Siraata", "(The) path", "ص ر ط", "Noun"),
                (1, "ٱلَّذِينَ", "allatheena", "(of) those", "ل ذ ي", "Relative Pronoun"),
                (2, "أَنْعَمْتَ", "an'amta", "You have bestowed favor", "ن ع م", "Verb"),
                (3, "عَلَيْهِمْ", "'alayhim", "upon them", "ع ل ي", "Preposition"),
                (4, "غَيْرِ", "ghayri", "not", "غ ي ر", "Noun"),
                (5, "ٱلْمَغْضُوبِ", "al-maghdoobi", "(of those) who earned (Your) anger", "غ ض ب", "Noun"),
                (6, "عَلَيْهِمْ", "'alayhim", "upon them", "ع ل ي", "Preposition"),
                (7, "وَلَا", "wala", "and not", "و ل ي", "Conjunction"),
                (8, "ٱلضَّآلِّينَ", "ad-daaalleen", "(of) the astray", "ض ل ل", "Noun"),
            ]
        }
        
        # Process Al-Fatihah
        try:
            surah1 = Surah.objects.get(number=1)
            for ayah_num, words_data in fatihah_words.items():
                try:
                    ayah = Ayah.objects.get(surah=surah1, number_in_surah=ayah_num)
                    for word_index, arabic, translit, meaning, root, pos in words_data:
                        WordMeaning.objects.update_or_create(
                            ayah=ayah,
                            word_index=word_index,
                            defaults={
                                'arabic_word': arabic,
                                'transliteration': translit,
                                'meaning_en': meaning,
                                'root_word': root,
                                'part_of_speech': pos,
                                'pronunciation_audio': f"https://quranwbw.com/audio/1/{ayah_num}/{word_index + 1}.mp3"
                            }
                        )
                except Ayah.DoesNotExist:
                    continue
            
            self.stdout.write("✅ Created detailed word meanings for Surah Al-Fatihah")
            
        except Exception as e:
            self.stdout.write(f"Error creating Al-Fatihah word meanings: {e}")
        
        # Create basic word meanings for Al-Baqarah (first 5 ayahs)
        try:
            surah2 = Surah.objects.get(number=2)
            alif_laam_meem = [
                (0, "الم", "Alif Laam Meem", "These are letters from the Arabic alphabet", "ا ل م", "Letter"),
            ]
            
            for ayah_num in range(1, 6):
                try:
                    ayah = Ayah.objects.get(surah=surah2, number_in_surah=ayah_num)
                    
                    if ayah_num == 1:
                        # First ayah is just "الم"
                        words_data = alif_laam_meem
                    else:
                        # For other ayahs, split the Arabic text
                        arabic_text = ayah.text_uthmani
                        if arabic_text:
                            words = arabic_text.split()
                            words_data = []
                            for i, word in enumerate(words):
                                words_data.append((
                                    i,
                                    word,
                                    f"word_{i+1}",
                                    f"Meaning of word {i+1} in Ayah {ayah_num}",
                                    "N/A",
                                    ""
                                ))
                        else:
                            continue
                    
                    for word_index, arabic, translit, meaning, root, pos in words_data:
                        WordMeaning.objects.update_or_create(
                            ayah=ayah,
                            word_index=word_index,
                            defaults={
                                'arabic_word': arabic,
                                'transliteration': translit,
                                'meaning_en': meaning,
                                'root_word': root,
                                'part_of_speech': pos,
                                'pronunciation_audio': f"https://quranwbw.com/audio/2/{ayah_num}/{word_index + 1}.mp3"
                            }
                        )
                        
                except Ayah.DoesNotExist:
                    continue
            
            self.stdout.write("✅ Created word meanings for Surah Al-Baqarah (first 5 ayahs)")
            
        except Exception as e:
            self.stdout.write(f"Error creating Al-Baqarah word meanings: {e}")

    # Helper methods for Arabic text processing
    def split_arabic_text(self, text):
        """Split Arabic text into words, handling Arabic diacritics"""
        if not text:
            return []
        
        # Remove extra whitespace and normalize
        text = text.strip()
        
        # Split by spaces (Arabic uses regular spaces)
        words = text.split()
        
        # Clean each word
        cleaned_words = []
        for word in words:
            # Remove extra diacritics that might cause issues
            cleaned = word.strip()
            if cleaned:
                cleaned_words.append(cleaned)
        
        return cleaned_words

    def generate_transliteration(self, arabic_word):
        """Generate basic transliteration for Arabic word"""
        # Very basic transliteration mapping
        # In a real application, you would use a proper Arabic transliteration library
        translit_map = {
            'ا': 'a', 'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j',
            'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'dh', 'ر': 'r',
            'ز': 'z', 'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'd',
            'ط': 't', 'ظ': 'dh', 'ع': 'a', 'غ': 'gh', 'ف': 'f',
            'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
            'ه': 'h', 'و': 'w', 'ي': 'y', 'ء': "'",
            'آ': 'aa', 'أ': 'a', 'إ': 'i', 'ؤ': "'u", 'ئ': "'i",
            'ة': 'h', 'ى': 'a', 'لا': 'la'
        }
        
        # Simple transliteration
        translit = ''
        for char in arabic_word:
            if char in translit_map:
                translit += translit_map[char]
            elif char in 'ًٌٍََُِّْ':  # Arabic diacritics
                continue  # Skip diacritics for basic transliteration
            else:
                translit += char
        
        return translit

    def get_word_meaning(self, arabic_word):
        """Get basic meaning for common Arabic words"""
        # Common Quranic words dictionary
        common_words = {
            'اللّٰهُ': 'Allah',
            'رَبّ': 'Lord',
            'الرَّحْمَٰنِ': 'The Most Gracious',
            'الرَّحِيمِ': 'The Most Merciful',
            'الْحَمْدُ': 'All praise',
            'عَلَى': 'upon',
            'وَ': 'and',
            'فِي': 'in',
            'مِن': 'from',
            'إِلَى': 'to',
            'عَن': 'about',
            'على': 'on',
            'كَانَ': 'was',
            'قَالَ': 'said',
            'رَأَى': 'saw',
            'سَمِعَ': 'heard',
            'عَلِمَ': 'knew',
            'يَعْلَمُ': 'knows',
            'يَقُولُ': 'says',
            'يَرَى': 'sees',
            'يَسْمَعُ': 'hears',
            'كِتَابٌ': 'book',
            'قُرْآنٌ': 'Quran',
            'نُورٌ': 'light',
            'ظُلْمٌ': 'darkness',
            'حَقٌّ': 'truth',
            'بَاطِلٌ': 'falsehood',
            'خَيْرٌ': 'good',
            'شَرٌّ': 'evil',
            'جَنَّةٌ': 'paradise',
            'نَارٌ': 'fire',
        }
        
        # Clean the word for lookup
        cleaned_word = arabic_word.strip('ًٌٍََُِّْ')
        
        if cleaned_word in common_words:
            return common_words[cleaned_word]
        else:
            return f"Meaning of '{arabic_word[:10]}...'"

    def extract_root(self, arabic_word):
        """Extract root letters from Arabic word (simplified)"""
        # Arabic root patterns (common triliteral roots)
        common_roots = {
            'ك ت ب': ['كَتَبَ', 'يَكْتُبُ', 'كِتَابٌ', 'مَكْتَبٌ', 'كَاتِبٌ'],
            'ع ل م': ['عَلِمَ', 'يَعْلَمُ', 'عِلْمٌ', 'عَالِمٌ', 'مَعْلُومٌ'],
            'ق و ل': ['قَالَ', 'يَقُولُ', 'قَوْلٌ', 'مَقَالٌ', 'قَائِلٌ'],
            'ر ح م': ['رَحِمَ', 'يَرْحَمُ', 'رَحْمَةٌ', 'رَحِيمٌ', 'رَحْمَانٌ'],
            'ع ب د': ['عَبَدَ', 'يَعْبُدُ', 'عِبَادَةٌ', 'عَابِدٌ', 'مَعْبُودٌ'],
            'ح م د': ['حَمِدَ', 'يَحْمَدُ', 'حَمْدٌ', 'حَامِدٌ', 'مَحْمُودٌ'],
            'ص ل ى': ['صَلَّى', 'يُصَلِّي', 'صَلَاةٌ', 'مُصَلٍّ', 'مُصَلَّى'],
            'ز ك ى': ['زَكَّى', 'يُزَكِّي', 'زَكَاةٌ', 'زَكِيٌّ', 'مُزَكًّى'],
        }
        
        # Check if word matches any root pattern
        cleaned_word = arabic_word.strip('ًٌٍََُِّْ')
        
        for root, derivatives in common_roots.items():
            if cleaned_word in derivatives:
                return root
        
        # If no match found, return first three unique letters
        letters = []
        for char in cleaned_word:
            if char.isalpha() and char not in letters:
                letters.append(char)
                if len(letters) >= 3:
                    break
        
        if len(letters) >= 3:
            return ' '.join(letters[:3])
        else:
            return 'N/A'
            """Create sample word meanings for first surah"""
            self.stdout.write("Creating word meanings for Al-Fatihah...")
            
            try:
                surah = Surah.objects.get(number=1)
                ayahs = Ayah.objects.filter(surah=surah)
                
                # Word meanings for Al-Fatihah
                word_meanings_data = [
                    # Ayah 1
                    (1, 0, "بِسْمِ", "bismi", "In the name of", "ب س م"),
                    (1, 1, "ٱللَّهِ", "Allahi", "Allah", "ا ل ه"),
                    (1, 2, "ٱلرَّحْمَٰنِ", "Ar-Rahman", "The Entirely Merciful", "ر ح م"),
                    (1, 3, "ٱلرَّحِيمِ", "Ar-Raheem", "The Especially Merciful", "ر ح م"),
                    
                    # Ayah 2
                    (2, 0, "ٱلْحَمْدُ", "Alhamdu", "All praise", "ح م د"),
                    (2, 1, "لِلَّهِ", "lillahi", "is for Allah", "ل ل ه"),
                    (2, 2, "رَبِّ", "Rabb", "Lord", "ر ب ب"),
                    (2, 3, "ٱلْعَٰلَمِينَ", "al-'aalameen", "of the worlds", "ع ل م"),
                ]
                
                for ayah_num, word_index, arabic, transliteration, meaning, root in word_meanings_data:
                    ayah = ayahs.get(number_in_surah=ayah_num)
                    WordMeaning.objects.create(
                        ayah=ayah,
                        word_index=word_index,
                        arabic_word=arabic,
                        transliteration=transliteration,
                        meaning_en=meaning,
                        root_word=root,
                        pronunciation_audio=f"https://quranwbw.com/audio/1/{ayah_num}/{word_index + 1}.mp3"
                    )
                
                self.stdout.write(self.style.SUCCESS("✅ Created word meanings"))
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not create word meanings: {e}"))
    
    def calculate_page(self, surah, ayah):
        """Simplified page calculation"""
        # This is a simplified version - in production, use actual page data
        if surah == 1:
            return 1
        elif surah == 2 and ayah <= 141:
            return 2
        else:
            return max(1, (surah - 1) // 2 + 1)
    
    def calculate_juz(self, surah, ayah):
        """Simplified juz calculation"""
        if surah == 1:
            return 1
        elif surah == 2 and ayah <= 141:
            return 1
        elif surah == 2 and ayah <= 252:
            return 2
        else:
            return min(30, (surah - 1) // 4 + 1)
    
    def calculate_hizb(self, surah, ayah):
        """Simplified hizb calculation"""
        return max(1, self.calculate_juz(surah, ayah) * 2 - 1)