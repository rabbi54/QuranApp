from django.shortcuts import get_object_or_404
import requests
import json
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm
from quran.models import Surah, Ayah, Recitation, WordMeaning

class Command(BaseCommand):
    help = 'Download complete Bangla Translation data from open-source APIs'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Bangla Translation data download..."))
        
        with transaction.atomic():
            self.download_bn_trans()
        
        self.stdout.write(self.style.SUCCESS("✅ Bangla Translation data download completed!"))
        self.stdout.write(f"📖 Surahs: {Surah.objects.count()}")
        self.stdout.write(f"🕌 Ayahs: {Ayah.objects.count()}")

    def download_bn_trans(self):
            self.stdout.write("Downloading bangla translations...")
            for surah_num in range(1, 115):
                try:
                    self.stdout.write(f"Downloading bangla translations for Surah {surah_num}...")
                    self.download_surah_verses(surah_num)
                    time.sleep(0.5)  # Rate limiting
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error downloading Surah {surah_num}: {e}"))
                    continue
        
    def download_surah_verses(self, surah_number):
        """Download all verses for a specific surah"""
        try:
            # Get Bangla translation
            bn_url = f"https://alquran-api.pages.dev/api/quran/surah/{surah_number}?lang=bn"
            response_bn = requests.get(bn_url, timeout=30)
            response_bn.raise_for_status()
            bn_data = response_bn.json()
            
            surah = Surah.objects.get(number=surah_number)
            surah.name_translation_bn = bn_data['translation']
            surah.save()
            updated_ayahs = []
            
            # Append Bangla Translation ayahs
            for i in range(len(bn_data['verses'])):
                verse_number = bn_data['verses'][i]['id']
                ayah = get_object_or_404(Ayah, surah=surah, number_in_surah=verse_number)
                ayah.translation_bn = bn_data['verses'][i]['translation']
                updated_ayahs.append(ayah)

            Ayah.objects.bulk_update(updated_ayahs, ['translation_bn'])                
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {len(bn_data['verses'])} verses for Surah {surah_number}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading verses for Surah {surah_number}: {e}"))
            # Create sample verses as fallback
            # self.create_sample_verses(surah_number)
    