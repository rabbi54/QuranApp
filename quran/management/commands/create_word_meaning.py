import requests
import json
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from quran.models import Surah, Ayah, WordMeaning

class Command(BaseCommand):
    help = 'Create word meanings for Quran verses'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Creating word meanings..."))
        
        with transaction.atomic():
            # Clear existing word meanings
            WordMeaning.objects.all().delete()
            
            # Create word meanings for first 114 surahs
            for surah_num in range(1, 115):
                self.create_surah_word_meanings(surah_num)
            
            self.stdout.write(self.style.SUCCESS("✅ Word meanings created successfully!"))
            self.stdout.write(f"📚 Total word meanings: {WordMeaning.objects.count()}")
    
    def create_surah_word_meanings(self, surah_number):
        """Create word meanings for a specific surah"""
        try:
            surah = Surah.objects.get(number=surah_number)
            ayahs = Ayah.objects.filter(surah=surah).order_by('number_in_surah')
            
            word_count = 0
            for ayah in ayahs:
                words_created = self.create_ayah_word_meanings(ayah)
                word_count += words_created
            
            self.stdout.write(f"  Created {word_count} word meanings for Surah {surah_number}: {surah.name_english}")
            
        except Surah.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Surah {surah_number} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing surah {surah_number}: {e}"))
    
    def create_ayah_word_meanings(self, ayah):
        """Create word meanings for a specific ayah"""
        if not ayah.text_uthmani:
            return 0
        
        # Parse Arabic text into words
        words = self.parse_arabic_text(ayah.text_uthmani)
        
        # Get pre-defined word meanings if available
        pre_defined = self.get_pre_defined_meanings(ayah.surah.number, ayah.number_in_surah)
        
        word_count = 0
        for i, arabic_word in enumerate(words):
            # Use pre-defined meaning if available, otherwise generate one
            if i < len(pre_defined):
                word_data = pre_defined[i]
            else:
                word_data = self.generate_word_data(arabic_word, i, ayah.surah.number, ayah.number_in_surah)
            
            # Create word meaning
            try:
                WordMeaning.objects.create(
                    ayah=ayah,
                    word_index=i,
                    arabic_word=word_data['arabic'],
                    transliteration=word_data['transliteration'],
                    meaning_en=word_data['meaning'],
                    root_word=word_data['root'],
                    part_of_speech=word_data['part_of_speech'],
                    pronunciation_audio=word_data['audio']
                )
                word_count += 1
            except Exception as e:
                self.stdout.write(f"    Error creating word {i} for ayah {ayah.number_in_surah}: {e}")
        
        return word_count
    
    def parse_arabic_text(self, text):
        """Parse Arabic text into individual words"""
        if not text:
            return []
        
        # Remove Arabic diacritics
        diacritics = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED]')
        clean_text = diacritics.sub('', text)
        
        # Split by spaces and filter empty strings
        words = clean_text.split()
        return [word.strip() for word in words if word.strip()]
    
    def get_pre_defined_meanings(self, surah_number, ayah_number):
        """Get pre-defined word meanings for common verses"""
        pre_defined_data = {
            # Surah Al-Fatihah (1)
            1: {
                1: [  # بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ
                    {'arabic': 'بِسْمِ', 'transliteration': 'bismi', 'meaning': 'In (the) name of', 'root': 'ب س م', 'part_of_speech': 'Preposition', 'audio': ''},
                    {'arabic': 'ٱللَّهِ', 'transliteration': 'Allahi', 'meaning': 'Allah', 'root': 'ا ل ه', 'part_of_speech': 'Proper Noun', 'audio': ''},
                    {'arabic': 'ٱلرَّحْمَٰنِ', 'transliteration': 'Ar-Rahman', 'meaning': 'The Entirely Merciful', 'root': 'ر ح م', 'part_of_speech': 'Proper Noun', 'audio': ''},
                    {'arabic': 'ٱلرَّحِيمِ', 'transliteration': 'Ar-Raheem', 'meaning': 'The Especially Merciful', 'root': 'ر ح م', 'part_of_speech': 'Proper Noun', 'audio': ''},
                ],
                2: [  # ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ
                    {'arabic': 'ٱلْحَمْدُ', 'transliteration': 'Alhamdu', 'meaning': 'All praise', 'root': 'ح م د', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'لِلَّهِ', 'transliteration': 'lillahi', 'meaning': 'is for Allah', 'root': 'ل ل ه', 'part_of_speech': 'Preposition', 'audio': ''},
                    {'arabic': 'رَبِّ', 'transliteration': 'Rabb', 'meaning': 'Lord', 'root': 'ر ب ب', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'ٱلْعَٰلَمِينَ', 'transliteration': 'al-\'aalameen', 'meaning': 'of the worlds', 'root': 'ع ل م', 'part_of_speech': 'Noun', 'audio': ''},
                ],
                3: [  # ٱلرَّحْمَٰنِ ٱلرَّحِيمِ
                    {'arabic': 'ٱلرَّحْمَٰنِ', 'transliteration': 'Ar-Rahman', 'meaning': 'The Entirely Merciful', 'root': 'ر ح م', 'part_of_speech': 'Proper Noun', 'audio': ''},
                    {'arabic': 'ٱلرَّحِيمِ', 'transliteration': 'Ar-Raheem', 'meaning': 'The Especially Merciful', 'root': 'ر ح م', 'part_of_speech': 'Proper Noun', 'audio': ''},
                ],
                4: [  # مَٰلِكِ يَوْمِ ٱلدِّينِ
                    {'arabic': 'مَٰلِكِ', 'transliteration': 'Maaliki', 'meaning': 'Sovereign', 'root': 'م ل ك', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'يَوْمِ', 'transliteration': 'Yawmi', 'meaning': '(of the) Day', 'root': 'ي و م', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'ٱلدِّينِ', 'transliteration': 'id-Deen', 'meaning': 'of Recompense', 'root': 'د ي ن', 'part_of_speech': 'Noun', 'audio': ''},
                ],
                5: [  # إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ
                    {'arabic': 'إِيَّاكَ', 'transliteration': 'Iyyaka', 'meaning': 'You alone', 'root': 'ا ي ي', 'part_of_speech': 'Pronoun', 'audio': ''},
                    {'arabic': 'نَعْبُدُ', 'transliteration': 'na\'budu', 'meaning': 'we worship', 'root': 'ع ب د', 'part_of_speech': 'Verb', 'audio': ''},
                    {'arabic': 'وَإِيَّاكَ', 'transliteration': 'wa iyyaka', 'meaning': 'and You alone', 'root': 'ا ي ي', 'part_of_speech': 'Conjunction', 'audio': ''},
                    {'arabic': 'نَسْتَعِينُ', 'transliteration': 'nasta\'een', 'meaning': 'we ask for help', 'root': 'ع و ن', 'part_of_speech': 'Verb', 'audio': ''},
                ],
                6: [  # ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ
                    {'arabic': 'ٱهْدِنَا', 'transliteration': 'Ihdina', 'meaning': 'Guide us', 'root': 'ه د ي', 'part_of_speech': 'Verb', 'audio': ''},
                    {'arabic': 'ٱلصِّرَٰطَ', 'transliteration': 'as-Siraat', 'meaning': 'to the straight path', 'root': 'ص ر ط', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'ٱلْمُسْتَقِيمَ', 'transliteration': 'al-Mustaqeem', 'meaning': 'the straight', 'root': 'ق و م', 'part_of_speech': 'Adjective', 'audio': ''},
                ],
                7: [  # صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ
                    {'arabic': 'صِرَٰطَ', 'transliteration': 'Siraata', 'meaning': 'The path', 'root': 'ص ر ط', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'ٱلَّذِينَ', 'transliteration': 'allatheena', 'meaning': 'of those', 'root': 'ل ذ ي', 'part_of_speech': 'Relative Pronoun', 'audio': ''},
                    {'arabic': 'أَنْعَمْتَ', 'transliteration': 'an\'amta', 'meaning': 'You have bestowed favor', 'root': 'ن ع م', 'part_of_speech': 'Verb', 'audio': ''},
                    {'arabic': 'عَلَيْهِمْ', 'transliteration': '\'alayhim', 'meaning': 'upon them', 'root': 'ع ل ي', 'part_of_speech': 'Preposition', 'audio': ''},
                    {'arabic': 'غَيْرِ', 'transliteration': 'ghayri', 'meaning': 'not', 'root': 'غ ي ر', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'ٱلْمَغْضُوبِ', 'transliteration': 'al-maghdoobi', 'meaning': 'those who have evoked anger', 'root': 'غ ض ب', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'وَلَا', 'transliteration': 'wala', 'meaning': 'and not', 'root': 'و ل ي', 'part_of_speech': 'Conjunction', 'audio': ''},
                    {'arabic': 'ٱلضَّآلِّينَ', 'transliteration': 'ad-daaalleen', 'meaning': 'those who are astray', 'root': 'ض ل ل', 'part_of_speech': 'Noun', 'audio': ''},
                ]
            },
            # Surah Al-Baqarah (2)
            2: {
                1: [  # الم
                    {'arabic': 'الم', 'transliteration': 'Alif Laam Meem', 'meaning': 'These are disjointed letters', 'root': 'ا ل م', 'part_of_speech': 'Letter', 'audio': ''},
                ],
                2: [  # ذَٰلِكَ الْكِتَابُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ
                    {'arabic': 'ذَٰلِكَ', 'transliteration': 'Zaalika', 'meaning': 'That', 'root': 'ذ ل ك', 'part_of_speech': 'Demonstrative Pronoun', 'audio': ''},
                    {'arabic': 'ٱلْكِتَابُ', 'transliteration': 'al-Kitaabu', 'meaning': 'the Book', 'root': 'ك ت ب', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'لَا', 'transliteration': 'laa', 'meaning': 'no', 'root': 'ل ي', 'part_of_speech': 'Negative Particle', 'audio': ''},
                    {'arabic': 'رَيْبَ', 'transliteration': 'rayba', 'meaning': 'doubt', 'root': 'ر ي ب', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'فِيهِ', 'transliteration': 'feehi', 'meaning': 'in it', 'root': 'ف ي ه', 'part_of_speech': 'Preposition', 'audio': ''},
                    {'arabic': 'هُدًى', 'transliteration': 'hudan', 'meaning': 'a guidance', 'root': 'ه د ي', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'لِّلْمُتَّقِينَ', 'transliteration': 'lilmuttaqeena', 'meaning': 'for the righteous', 'root': 'و ق ي', 'part_of_speech': 'Noun', 'audio': ''},
                ]
            },
            # Surah Ali 'Imran (3)
            3: {
                1: [  # الم
                    {'arabic': 'الم', 'transliteration': 'Alif Laam Meem', 'meaning': 'These are disjointed letters', 'root': 'ا ل م', 'part_of_speech': 'Letter', 'audio': ''},
                ]
            },
            # Surah An-Nisa (4)
            4: {
                1: [  # يَٰٓأَيُّهَا ٱلنَّاسُ ٱتَّقُوا۟ رَبَّكُمُ ٱلَّذِى خَلَقَكُم مِّن نَّفْسٍ وَٰحِدَةٍ
                    {'arabic': 'يَٰٓأَيُّهَا', 'transliteration': 'Yaa ayyuha', 'meaning': 'O', 'root': 'ي ا ه', 'part_of_speech': 'Vocative Particle', 'audio': ''},
                    {'arabic': 'ٱلنَّاسُ', 'transliteration': 'an-Naasu', 'meaning': 'mankind', 'root': 'ن و س', 'part_of_speech': 'Noun', 'audio': ''},
                    {'arabic': 'ٱتَّقُوا۟', 'transliteration': 'ittaqoo', 'meaning': 'fear', 'root': 'و ق ي', 'part_of_speech': 'Verb', 'audio': ''},
                    {'arabic': 'رَبَّكُمُ', 'transliteration': 'Rabbakum', 'meaning': 'your Lord', 'root': 'ر ب ب', 'part_of_speech': 'Noun', 'audio': ''},
                ]
            }
        }
        
        # Return pre-defined data if available
        if surah_number in pre_defined_data and ayah_number in pre_defined_data[surah_number]:
            return pre_defined_data[surah_number][ayah_number]
        
        return []
    
    def generate_word_data(self, arabic_word, word_index, surah_number, ayah_number):
        """Generate word data for unknown words"""
        return {
            'arabic': arabic_word,
            'transliteration': self.generate_transliteration(arabic_word, word_index),
            'meaning': self.get_word_meaning(arabic_word),
            'root': self.extract_root(arabic_word),
            'part_of_speech': self.guess_part_of_speech(arabic_word),
            'audio': self.generate_audio_url(surah_number, ayah_number, word_index)
        }
    
    def generate_transliteration(self, arabic_word, word_index):
        """Generate basic transliteration"""
        # Basic transliteration mapping
        translit_map = {
            'ا': 'a', 'أ': 'a', 'إ': 'i', 'آ': 'aa', 'ى': 'a',
            'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'h',
            'خ': 'kh', 'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z',
            'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'd', 'ط': 't',
            'ظ': 'dh', 'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
            'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h',
            'و': 'w', 'ي': 'y', 'ة': 'h', 'ء': "'", 'ؤ': "'u",
            'ئ': "'i", 'لا': 'la'
        }
        
        result = []
        for char in arabic_word:
            if char in translit_map:
                result.append(translit_map[char])
            elif char in 'ًٌٍََُِّْ':  # Skip Arabic diacritics
                continue
            else:
                result.append(char)
        
        translit = ''.join(result)
        return translit if translit else f"word_{word_index + 1}"
    
    def get_word_meaning(self, arabic_word):
        """Get meaning from dictionary"""
        # Quranic words dictionary
        quranic_dict = {
            'الله': 'Allah (God)',
            'رب': 'Lord',
            'رحمن': 'Most Gracious',
            'رحيم': 'Most Merciful',
            'الحمد': 'All praise',
            'عالمين': 'Worlds',
            'ملك': 'King/Master',
            'يوم': 'Day',
            'الدين': 'Judgment/Recompense',
            'إياك': 'You alone',
            'نعبد': 'We worship',
            'نستعين': 'We seek help',
            'اهدنا': 'Guide us',
            'الصراط': 'The path',
            'المستقيم': 'Straight',
            'الذين': 'Those who',
            'أنعمت': 'You have favored',
            'عليهم': 'Upon them',
            'غير': 'Not',
            'المغضوب': 'Those who earned anger',
            'الضالين': 'Those who are astray',
            'بسم': 'In the name of',
            'كتاب': 'Book',
            'لا': 'No/Not',
            'ريب': 'Doubt',
            'فيه': 'In it',
            'هدى': 'Guidance',
            'للمتقين': 'For the righteous',
            'الناس': 'Mankind',
            'اتقوا': 'Fear',
            'خلقكم': 'Created you',
            'نفس': 'Soul',
            'واحدة': 'One',
            'و': 'And',
            'من': 'From',
            'هو': 'He',
            'هم': 'They',
            'أنت': 'You',
            'أنا': 'I',
            'نحن': 'We',
            'هذا': 'This',
            'ذلك': 'That',
            'هؤلاء': 'These',
            'أولئك': 'Those',
            'كان': 'Was',
            'يكون': 'Will be',
            'يكونون': 'They will be',
            'قال': 'Said',
            'يقول': 'Says',
            'قالوا': 'They said',
            'تعالى': 'Exalted',
            'عظيم': 'Great',
            'كريم': 'Generous',
            'حكيم': 'Wise',
            'عليم': 'All-Knowing',
            'قدير': 'All-Powerful',
            'سميع': 'All-Hearing',
            'بصير': 'All-Seeing',
            'غفور': 'Forgiving',
            'رحيم': 'Merciful',
            'عزيز': 'Mighty',
            'حكيم': 'Wise',
        }
        
        # Clean the word
        clean_word = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', arabic_word)
        
        # Check exact match
        if clean_word in quranic_dict:
            return quranic_dict[clean_word]
        
        # Check without definite article
        if clean_word.startswith('ال'):
            base_word = clean_word[2:]
            if base_word in quranic_dict:
                return quranic_dict[base_word]
        
        # Check for common patterns
        for key, value in quranic_dict.items():
            if key in clean_word:
                return value
        
        return "Meaning not available"
    
    def extract_root(self, arabic_word):
        """Extract root letters from Arabic word"""
        # Common Arabic roots
        common_roots = {
            'علم': ['عالم', 'علامة', 'تعليم', 'معلم', 'عليم'],
            'كتب': ['كتاب', 'مكتب', 'كاتب', 'مكتوب', 'يكتب'],
            'قول': ['قال', 'يقول', 'قائل', 'مقول', 'قول'],
            'عبد': ['عابد', 'عبادة', 'معبود', 'يعبد', 'عبد'],
            'حمد': ['حامد', 'حمدة', 'محمود', 'يحمد', 'حمد'],
            'صلى': ['مصلى', 'صلاة', 'مصلي', 'يصلي', 'صلى'],
            'زكى': ['زكاة', 'زكي', 'مزكى', 'يزكي', 'زكى'],
            'رحم': ['رحمن', 'رحيب', 'راحة', 'مرحوم', 'رحم'],
            'رب': ['رب', 'ربوبية', 'تربية', 'رباني'],
            'دين': ['دين', 'مدين', 'ديني', 'تدين'],
            'نفس': ['نفس', 'أنفس', 'نفسي', 'نفوس'],
            'خلق': ['خلق', 'يخلق', 'مخلوق', 'خلاق'],
            'هدى': ['هدى', 'يهدي', 'مهتد', 'هداية'],
            'صبر': ['صبر', 'يصبر', 'صابر', 'صبر'],
            'شكر': ['شكر', 'يشكر', 'شاكر', 'شكر'],
            'صلاة': ['صلاة', 'مصلي', 'يصلي', 'صلاة'],
            'زكاة': ['زكاة', 'يزكي', 'زكي', 'زكاة'],
        }
        
        clean_word = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', arabic_word)
        
        for root, derivatives in common_roots.items():
            for derivative in derivatives:
                if derivative in clean_word:
                    return root
        
        # Extract first three unique letters
        letters = []
        for char in clean_word:
            if char.isalpha() and char not in letters:
                letters.append(char)
                if len(letters) >= 3:
                    return ' '.join(letters[:3])
        
        if letters:
            return ' '.join(letters)
        
        return "N/A"
    
    def guess_part_of_speech(self, arabic_word):
        """Guess part of speech"""
        clean_word = re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED]', '', arabic_word)
        
        # Common patterns
        if clean_word.startswith('ال'):
            return "Noun"
        elif clean_word.endswith('ة'):
            return "Noun (Feminine)"
        elif clean_word.endswith('ون') or clean_word.endswith('ين'):
            return "Noun (Plural)"
        elif len(clean_word) <= 2:
            if clean_word in ['و', 'ف', 'ثم', 'أو', 'بل', 'لكن']:
                return "Conjunction"
            elif clean_word in ['في', 'من', 'عن', 'على', 'إلى', 'ب', 'ك', 'ل']:
                return "Preposition"
            elif clean_word in ['لا', 'لم', 'لن', 'ما', 'إن', 'أن']:
                return "Particle"
            else:
                return "Particle"
        elif 'ي' in clean_word and 'ن' in clean_word:
            return "Verb"
        else:
            return "Noun"
    
    def generate_audio_url(self, surah_number, ayah_number, word_index):
        """Generate audio URL for word pronunciation"""
        # In a real application, you would use actual audio files
        # For now, return empty string
        return ""