import CONFIG from './config.js';
import { showToast } from './utilities.js';

class BismillahManager {
    constructor() {
        this.bismillahData = null;
        this.isBismillahVisible = false;
        this.currentReciter = 'Alafasy';
    }

    async loadBismillah() {
        try {
            const response = await fetch(CONFIG.API_ENDPOINTS.BISMILLAH);
            if (!response.ok) throw new Error('Failed to load Bismillah');
            this.bismillahData = await response.json();
            return this.bismillahData;
        } catch (error) {
            console.error('Error loading Bismillah:', error);
            // Fallback to default Bismillah data
            this.bismillahData = this.getDefaultBismillah();
            return this.bismillahData;
        }
    }

    getDefaultBismillah() {
        return {
            text_uthmani: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
            translation_en: 'In the name of Allah, the Entirely Merciful, the Especially Merciful.',
            audio_url: CONFIG.BISMILLAH_AUDIO[this.currentReciter],
            words: [
                { index: 1, arabic: 'بِسْمِ', audio: 'https://words.audios.quranwbw.com/001/001_001_001.mp3' },
                { index: 2, arabic: 'اللَّهِ', audio: 'https://words.audios.quranwbw.com/001/001_001_002.mp3' },
                { index: 3, arabic: 'الرَّحْمَٰنِ', audio: 'https://words.audios.quranwbw.com/001/001_001_003.mp3' },
                { index: 4, arabic: 'الرَّحِيمِ', audio: 'https://words.audios.quranwbw.com/001/001_001_004.mp3' }
            ]
        };
    }

    shouldShowBismillah(surahNumber) {
        return surahNumber !== 1 && surahNumber !== 9;
    }

    displayBismillah(surahNumber) {
        if (!this.shouldShowBismillah(surahNumber) || !this.bismillahData) {
            return null;
        }

        const container = document.createElement('div');
        container.className = 'bismillah-container';
        container.id = 'bismillah-container';

        container.innerHTML = `
            <div class="bismillah-display">
                <div class="bismillah-arabic">${this.bismillahData.text_uthmani}</div>
                <div class="bismillah-translation">${this.bismillahData.translation_en}</div>
                
                <div class="bismillah-words" style="display: none;">
                    ${this.bismillahData.words.map(word => `
                        <span class="word" data-index="${word.index}" 
                              onclick="bismillahManager.playWord(${word.index})">
                            ${word.arabic}
                        </span>
                    `).join(' ')}
                </div>
            </div>
        `;

        this.isBismillahVisible = true;
        return container;
    }

    playFullBismillah() {
        if (!this.bismillahData?.audio_url) return;
        
        const audio = new Audio(this.bismillahData.audio_url);
        audio.play().catch(e => {
            console.error('Bismillah audio failed:', e);
            showToast('Cannot play Bismillah audio', 'error');
        });
    }

    async playWordByWord() {
        if (!this.bismillahData?.words) return;
        
        const wordsContainer = document.querySelector('.bismillah-words');
        if (wordsContainer) wordsContainer.style.display = 'block';
        
        for (const word of this.bismillahData.words) {
            await this.playWordWithHighlight(word.index);
            await this.delay(500); // Pause between words
        }
        
        if (wordsContainer) wordsContainer.style.display = 'none';
    }

    playWord(index) {
        const word = this.bismillahData?.words?.find(w => w.index === index);
        if (!word?.audio) return;
        
        this.highlightWord(index);
        const audio = new Audio(word.audio);
        audio.play();
        
        audio.onended = () => this.unhighlightWord(index);
    }

    async playWordWithHighlight(index) {
        return new Promise((resolve) => {
            this.highlightWord(index);
            this.playWord(index);
            
            // Assume average word duration is 1 second
            setTimeout(() => {
                this.unhighlightWord(index);
                resolve();
            }, 1000);
        });
    }

    highlightWord(index) {
        document.querySelectorAll('.bismillah-words .word').forEach(span => {
            if (parseInt(span.dataset.index) === index) {
                span.classList.add('highlighted');
            }
        });
    }

    unhighlightWord(index) {
        document.querySelectorAll('.bismillah-words .word').forEach(span => {
            if (parseInt(span.dataset.index) === index) {
                span.classList.remove('highlighted');
            }
        });
    }

    toggleWordByWord() {
        const wordsContainer = document.querySelector('.bismillah-words');
        if (!wordsContainer) return;
        
        if (wordsContainer.style.display === 'none' || !wordsContainer.style.display) {
            wordsContainer.style.display = 'block';
            this.playWordByWord();
        } else {
            wordsContainer.style.display = 'none';
        }
    }

    changeReciter(reciter) {
        this.currentReciter = reciter;
        if (this.bismillahData) {
            this.bismillahData.audio_url = CONFIG.BISMILLAH_AUDIO[reciter];
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

export default BismillahManager;