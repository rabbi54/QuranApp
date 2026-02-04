import CONFIG from './config.js';
import { showToast, getCookie } from './utilities.js';

class WordModal {
    constructor() {
        this.modalBackdrop = document.getElementById('modal-backdrop');
        this.wordModal = document.getElementById('word-modal');
        this.audioElement = document.getElementById('word-audio-player');
        this.audioSource = document.getElementById('word-audio-source');
        this.init();
    }

    init() {
        if (this.modalBackdrop) {
            this.modalBackdrop.addEventListener('click', () => this.close());
        }
        
        const closeBtn = this.wordModal?.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
    }

    async showWordDetail(ayahId, wordIndex, surahNumber, ayahNumber, audioUrl) {
        const clickedWord = event?.target;
        
        // Extract formatted numbers
        let surahNumberFormatted = surahNumber;
        let ayahNumberFormatted = ayahNumber;
        let wordIndexFormatted = wordIndex;
        
        if (!surahNumberFormatted || !ayahNumberFormatted || !wordIndexFormatted) {
            if (clickedWord?.dataset) {
                surahNumberFormatted = clickedWord.dataset.surahNumber || surahNumber;
                ayahNumberFormatted = clickedWord.dataset.ayahNumber || ayahNumber;
                wordIndexFormatted = clickedWord.dataset.wordIndex || wordIndex;
            }
        }
        
        // Convert to raw numbers
        const surahNumberRaw = parseInt(surahNumberFormatted);
        const ayahNumberRaw = parseInt(ayahNumberFormatted);
        const wordIndexRaw = parseInt(wordIndexFormatted) - 1; // Convert to zero-based
        
        // Use provided audio URL or construct from data
        const finalAudioUrl = audioUrl || 
            `https://words.audios.quranwbw.com/${surahNumberRaw}/${surahNumberFormatted}_${ayahNumberFormatted}_${wordIndexFormatted}.mp3`;
        
        // Set up audio
        if (this.audioSource && this.audioElement) {
            this.audioSource.src = finalAudioUrl;
            this.audioElement.load();
        }
        
        // Try to fetch word details
        const endpoints = [
            CONFIG.API_ENDPOINTS.AYAH_WORD
                .replace('{ayahId}', ayahId)
                .replace('{wordIndex}', wordIndexRaw),
        ];
        
        await this.tryEndpoints(endpoints, ayahId, surahNumberRaw, ayahNumberRaw, wordIndexRaw, finalAudioUrl);
    }

    async tryEndpoints(endpoints, ayahId, surahNumber, ayahNumber, wordIndex, audioUrl) {
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint);
                if (!response.ok) continue;
                
                const wordData = await response.json();
                if (wordData.error) continue;
                
                this.displayWordData(wordData);
                this.open();
                
                // Auto-play if enabled
                const autoPlay = localStorage.getItem('autoPlayWordAudio') === 'true';
                if (autoPlay && this.audioElement) {
                    this.audioElement.play().catch(e => console.log('Auto-play prevented:', e));
                }
                
                return;
            } catch (error) {
                console.log(`Word endpoint ${endpoint} failed:`, error);
                continue;
            }
        }
        
        // If all endpoints fail, show basic info
        this.showBasicWordInfo(ayahId, surahNumber, ayahNumber, wordIndex, audioUrl);
    }

    displayWordData(wordData) {
        document.getElementById('word-arabic').textContent = wordData.arabic || 'N/A';
        document.getElementById('word-transliteration').textContent = wordData.transliteration || 'N/A';
        document.getElementById('word-meaning').textContent = wordData.meaning || 'Meaning not available';
        document.getElementById('word-root').textContent = wordData.root || 'N/A';
        
        const audioContainer = document.getElementById('word-audio-container');
        if (audioContainer) audioContainer.style.display = 'block';
    }

    showBasicWordInfo(ayahId, surahNumber, ayahNumber, wordIndex, audioUrl) {
        const verseElement = document.querySelector(`[data-ayah-id="${ayahId}"]`);
        if (!verseElement) return;
        
        const arabicText = verseElement.querySelector('.arabic-text')?.textContent;
        if (!arabicText) return;
        
        const words = arabicText.trim().split(/\s+/);
        if (wordIndex >= words.length) return;
        
        document.getElementById('word-arabic').textContent = words[wordIndex];
        document.getElementById('word-transliteration').textContent = `Word ${wordIndex + 1}`;
        document.getElementById('word-meaning').textContent = 'Detailed meaning not available';
        document.getElementById('word-root').textContent = 'N/A';
        
        const audioContainer = document.getElementById('word-audio-container');
        if (audioContainer) audioContainer.style.display = 'block';
        
        this.open();
    }

    open() {
        if (this.modalBackdrop) this.modalBackdrop.style.display = 'block';
        if (this.wordModal) this.wordModal.style.display = 'block';
    }

    close() {
        if (this.modalBackdrop) this.modalBackdrop.style.display = 'none';
        if (this.wordModal) this.wordModal.style.display = 'none';
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
        }
    }
}

export default WordModal;