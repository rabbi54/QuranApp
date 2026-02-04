import CONFIG from './config.js';
import { showToast, padNumber, getQuranWBWAudioUrl } from './utilities.js';

class SurahLoader {
    constructor() {
        this.currentSurah = null;
        this.currentVerses = [];
        this.currentPage = 1;
        this.versesPerPage = CONFIG.VERSES_PER_PAGE;
    }

    async loadSurahs() {
        try {
            const response = await fetch(CONFIG.API_ENDPOINTS.SURAHS);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const surahs = await response.json();
            this.populateSurahSelect(surahs);
        } catch (error) {
            console.error('Failed to load surahs:', error);
            showToast('Cannot load surahs. Please try again later.', 'error');
        }
    }

    populateSurahSelect(surahs) {
        const select = document.getElementById('surah-selector');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select Surah...</option>';
        
        surahs.forEach(surah => {
            const option = document.createElement('option');
            option.value = surah.number;
            option.textContent = `${surah.number}. ${surah.name_english || surah.name_en} 
                                ${surah.name_translation_bn ? `(${surah.name_translation_bn})` : ''}`;
            select.appendChild(option);
        });
        
        select.addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadSurah(parseInt(e.target.value));
            }
        });
    }

    async loadSurah(surahNumber) {
        const container = document.getElementById('verses-container');
        if (!container) return;
        
        container.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Loading verses...</div>';
        
        try {
            const response = await fetch(CONFIG.API_ENDPOINTS.SURAH.replace('{number}', surahNumber));
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.processSurahData(data, surahNumber);
            
        } catch (error) {
            console.error('Failed to load surah:', error);
            container.innerHTML = '<div class="loading">Error loading verses. Please try again later.</div>';
        }
    }

    processSurahData(data, surahNumber) {
        let verses = [];
        let surahData = null;
        
        if (Array.isArray(data)) {
            verses = data;
            if (verses.length > 0) {
                surahData = {
                    number: verses[0].surah,
                    name_english: verses[0].surah_name || `Surah ${verses[0].surah}`,
                    name_arabic: verses[0].surah_name_arabic || `سورة ${verses[0].surah}`
                };
            }
        } else if (data.verses) {
            verses = data.verses;
            surahData = data.surah;
        } else if (data.results) {
            verses = data.results;
            if (verses.length > 0) {
                surahData = {
                    number: verses[0].surah,
                    name_english: verses[0].surah_name || `Surah ${verses[0].surah}`,
                    name_arabic: verses[0].surah_name_arabic || `سورة ${verses[0].surah}`
                };
            }
        } else {
            verses = [data];
        }
        
        if (verses.length === 0) {
            throw new Error('No verses found');
        }
        
        this.currentSurah = surahData || {
            number: surahNumber,
            name_english: `Surah ${surahNumber}`,
            name_arabic: `سورة ${surahNumber}`
        };
        
        this.currentVerses = verses;
        this.currentPage = 1;
        
        this.updateSurahHeader();
        this.displayPage();
        
        if (window.audioPlayer) {
            window.audioPlayer.buildPlaylist(verses, this.currentSurah);
        }
    }

    updateSurahHeader() {
        const title = document.querySelector('.surah-header h2');
        const arabicName = document.querySelector('.surah-header .arabic-name');
        
        if (title && this.currentSurah) {
            title.textContent = `${this.currentSurah.number}. ${this.currentSurah.name_english}`;
        }
        
        if (arabicName && this.currentSurah) {
            arabicName.textContent = this.currentSurah.name_arabic;
        }
    }

    displayPage() {
        const container = document.getElementById('verses-container');
        if (!container) return;
        
        const startIndex = (this.currentPage - 1) * this.versesPerPage;
        const endIndex = startIndex + this.versesPerPage;
        const pageVerses = this.currentVerses.slice(startIndex, endIndex);
        
        container.innerHTML = '';
        
        if (pageVerses.length === 0) {
            container.innerHTML = '<div class="loading">No verses found.</div>';
            return;
        }
        
        pageVerses.forEach((verse, index) => {
            const globalIndex = startIndex + index;
            const verseDiv = this.createVerseElement(verse, globalIndex);
            container.appendChild(verseDiv);
        });
        
        this.updatePagination();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    createVerseElement(verse, index) {
        const verseDiv = document.createElement('div');
        verseDiv.className = 'verse';
        verseDiv.dataset.index = index;
        verseDiv.dataset.ayahId = verse.id;
        verseDiv.dataset.surah = verse.surah;
        verseDiv.dataset.ayah = verse.number_in_surah;
        
        // Verse header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'verse-header';
        
        const verseNumber = document.createElement('div');
        verseNumber.className = 'verse-number';
        verseNumber.textContent = verse.number_in_surah;
        
        const verseInfo = document.createElement('div');
        verseInfo.className = 'verse-info';
        verseInfo.textContent = `Surah ${verse.surah_name || verse.surah}, Ayah ${verse.number_in_surah} | Page ${verse.page_number || 'N/A'} | Juz ${verse.juz_number || 'N/A'}`;
        
        headerDiv.appendChild(verseNumber);
        headerDiv.appendChild(verseInfo);
        
        // Arabic text
        const arabicDiv = document.createElement('div');
        arabicDiv.className = 'arabic-text';
        
        const arabicText = verse.text_uthmani_cleaned || verse.text_indopak || verse.text_imlaei || verse.text || '';
        const words = verse.words || [];
        
        if (words.length > 0) {
            this.renderWordsWithData(arabicDiv, words, verse);
        } else {
            this.renderWordsFromText(arabicDiv, arabicText, verse);
        }
        
        // Translation
        const translationDiv = document.createElement('div');
        translationDiv.className = 'translation';
        translationDiv.innerHTML = `<strong>Translation:</strong> ${verse.translation_en || 'Translation not available'}`;
        
        if (verse.translation_bn) {
            translationDiv.innerHTML += `<br><strong>Bangla:</strong> ${verse.translation_bn}`;
        }
        
        // Controls
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'verse-controls';
        controlsDiv.innerHTML = `
            <button onclick="surahLoader.playAyah(${index})" class="verse-play-btn" title="Play this verse">
                <i class="fas fa-play"></i> Play
            </button>
            <button onclick="surahLoader.copyAyah(${index})" title="Copy verse">
                <i class="fas fa-copy"></i> Copy
            </button>
            <button onclick="surahLoader.bookmarkAyah('${verse.id}')" title="Bookmark this verse">
                <i class="fas fa-bookmark"></i> Save
            </button>
            <button onclick="surahLoader.shareAyah(${index})" title="Share this verse">
                <i class="fas fa-share"></i> Share
            </button>
        `;
        
        verseDiv.appendChild(headerDiv);
        verseDiv.appendChild(arabicDiv);
        verseDiv.appendChild(translationDiv);
        verseDiv.appendChild(controlsDiv);
        
        return verseDiv;
    }

    renderWordsWithData(container, words, verse) {
        words.forEach((word, wordIndex) => {
            const wordSpan = this.createWordSpan(verse, wordIndex + 1, word.arabic_word || word.arabic);
            container.appendChild(wordSpan);
        });
    }

    renderWordsFromText(container, arabicText, verse) {
        const arabicWords = arabicText.split(' ');
        arabicWords.forEach((word, wordIndex) => {
            const wordSpan = this.createWordSpan(verse, wordIndex + 1, word);
            container.appendChild(wordSpan);
        });
    }

    createWordSpan(verse, wordIndex, arabicWord) {
        const surahNumber = verse.surah;
        const ayahNumber = verse.number_in_surah;
        
        const surahPadded = padNumber(surahNumber);
        const ayahPadded = padNumber(ayahNumber);
        const wordPadded = padNumber(wordIndex);
        
        const wordSpan = document.createElement('span');
        wordSpan.className = 'word';
        wordSpan.dataset.wordIndex = wordPadded;
        wordSpan.dataset.ayahId = verse.id;
        wordSpan.dataset.surahNumber = surahPadded;
        wordSpan.dataset.ayahNumber = ayahPadded;
        wordSpan.dataset.actualIndex = wordIndex;
        
        // Get QuranWBW audio URL
        const audioUrl = getQuranWBWAudioUrl(surahNumber, ayahNumber, wordIndex);
        wordSpan.dataset.audioUrl = audioUrl;
        
        const wordText = document.createTextNode(arabicWord + ' ');
        wordSpan.appendChild(wordText);
        
        wordSpan.style.direction = 'rtl';
        wordSpan.style.unicodeBidi = 'embed';
        
        wordSpan.onclick = () => {
            if (window.wordModal) {
                window.wordModal.showWordDetail(
                    verse.id,
                    wordPadded,
                    surahPadded,
                    ayahPadded,
                    audioUrl
                );
            }
        };
        
        return wordSpan;
    }

    updatePagination() {
        const totalPages = Math.ceil(this.currentVerses.length / this.versesPerPage);
        const pageInfo = document.getElementById('page-info');
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        
        if (pageInfo) pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
        if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;
    }

    nextPage() {
        const totalPages = Math.ceil(this.currentVerses.length / this.versesPerPage);
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.displayPage();
        }
    }

    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.displayPage();
        }
    }

    goToAyah() {
        const input = document.getElementById('go-to-ayah');
        if (!input) return;
        
        const ayahNumber = parseInt(input.value);
        if (!ayahNumber || ayahNumber < 1) {
            showToast('Please enter a valid ayah number', 'warning');
            return;
        }
        
        const verseIndex = this.currentVerses.findIndex(v => v.number_in_surah === ayahNumber);
        if (verseIndex === -1) {
            showToast(`Ayah ${ayahNumber} not found in this surah`, 'warning');
            return;
        }
        
        const targetPage = Math.floor(verseIndex / this.versesPerPage) + 1;
        
        if (targetPage !== this.currentPage) {
            this.currentPage = targetPage;
            this.displayPage();
        }
        
        setTimeout(() => {
            const verseElement = document.querySelector(`.verse[data-index="${verseIndex}"]`);
            if (verseElement) {
                verseElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                verseElement.style.backgroundColor = 'rgba(44, 164, 171, 0.1)';
                setTimeout(() => {
                    verseElement.style.backgroundColor = '';
                }, 2000);
            }
        }, 100);
    }

    playAyah(verseIndex) {
        if (window.audioPlayer) {
            window.audioPlayer.playAyah(verseIndex);
        }
    }

    copyAyah(verseIndex) {
        const verse = this.currentVerses[verseIndex];
        if (!verse || !this.currentSurah) return;
        
        let textToCopy = `Surah ${this.currentSurah.name_english} (${this.currentSurah.number}:${verse.number_in_surah})\n\n`;
        textToCopy += `Arabic: ${verse.text_uthmani || verse.text}\n\n`;
        textToCopy += `Translation: ${verse.translation_en || 'Translation not available'}\n\n`;
        if (verse.translation_bn) {
            textToCopy += `Bangla: ${verse.translation_bn}\n\n`;
        }
        
        navigator.clipboard.writeText(textToCopy)
            .then(() => showToast('Verse copied to clipboard!', 'success'))
            .catch(err => {
                console.error('Copy failed:', err);
                showToast('Failed to copy. Please try again.', 'error');
            });
    }

    async bookmarkAyah(ayahId) {
        try {
            const response = await fetch('/api/bookmarks/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ ayah: ayahId, bookmark_type: 'default' })
            });
            
            if (response.ok) {
                showToast('Verse bookmarked!', 'success');
            } else if (response.status === 401) {
                showToast('Please login to bookmark verses', 'warning');
            } else {
                throw new Error('Bookmark failed');
            }
        } catch (error) {
            console.error('Error bookmarking:', error);
            showToast('Could not bookmark verse', 'error');
        }
    }

    shareAyah(verseIndex) {
        const verse = this.currentVerses[verseIndex];
        if (!verse || !this.currentSurah) return;
        
        const shareText = `Surah ${this.currentSurah.name_english} ${verse.number_in_surah}: ${verse.text_uthmani || verse.text}\n\n${verse.translation_en || ''}\n\nShared via Quran App`;
        
        if (navigator.share) {
            navigator.share({
                title: `Quran - ${this.currentSurah.name_english} ${verse.number_in_surah}`,
                text: shareText,
                url: window.location.href
            });
        } else {
            navigator.clipboard.writeText(shareText)
                .then(() => showToast('Verse link copied to clipboard!', 'success'))
                .catch(() => showToast('Sharing not supported on this device', 'warning'));
        }
    }
}

export default SurahLoader;