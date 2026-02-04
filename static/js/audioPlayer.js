import CONFIG from './config.js';
import { showToast, formatTime } from './utilities.js';

class AudioPlayer {
    constructor() {
        this.audio = document.getElementById('quran-audio');
        this.isPlaying = false;
        this.currentVerseIndex = -1;
        this.currentVerse = null;
        this.repeatMode = false;
        this.volume = 0.8;
        this.isMuted = false;
        this.playbackSpeed = 1.0;
        this.isMinimized = false;
        this.playlist = [];
        this.currentSurah = null;
        
        this.init();
    }

    init() {
        if (!this.audio) {
            console.error('Audio element not found');
            return;
        }
        
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('play', () => this.onPlay());
        this.audio.addEventListener('pause', () => this.onPause());
        this.audio.addEventListener('ended', () => this.onAudioEnded());
        
        this.audio.volume = this.volume;
        this.audio.playbackRate = this.playbackSpeed;
        
        // Set up event listeners for player controls
        this.setupEventListeners();
    }

    setupEventListeners() {
        const playBtn = document.getElementById('play-btn');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const repeatBtn = document.getElementById('repeat-btn');
        const muteBtn = document.getElementById('volume-btn');
        const speedBtn = document.getElementById('speed-btn');
        const progressBar = document.getElementById('progress-bar');
        const minimizeBtn = document.getElementById('minimize-btn');
        
        if (playBtn) playBtn.addEventListener('click', () => this.togglePlay());
        if (prevBtn) prevBtn.addEventListener('click', () => this.previousAyah());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextAyah());
        if (repeatBtn) repeatBtn.addEventListener('click', () => this.toggleRepeat());
        if (muteBtn) muteBtn.addEventListener('click', () => this.toggleMute());
        if (speedBtn) speedBtn.addEventListener('click', () => this.toggleSpeed());
        if (progressBar) progressBar.addEventListener('click', (e) => this.seekAudio(e));
        if (minimizeBtn) minimizeBtn.addEventListener('click', () => this.toggleMinimize());
    }

    buildPlaylist(verses, surah) {
        this.playlist = verses.map((verse, index) => ({
            index: index,
            surah: verse.surah || surah.number,
            surahName: verse.surah_name || surah.name_english,
            ayahNumber: verse.number_in_surah,
            arabicText: verse.text_uthmani || verse.text,
            duration: 0,
            verse: verse
        }));
        this.currentSurah = surah;
    }

    playAyah(verseIndex) {
        const verse = this.playlist[verseIndex]?.verse;
        if (!verse) return;
        
        this.currentVerseIndex = verseIndex;
        this.currentVerse = verse;
        
        this.updatePlayerInfo(verse);
        
        const surahNum = padNumber(verse.surah, 3);
        const ayahNum = padNumber(verse.number_in_surah, 3);
        const audioUrl = `${CONFIG.EVERY_AYAH_BASE_URL}/Alafasy_128kbps/${surahNum}${ayahNum}.mp3`;
        
        this.audio.src = audioUrl;
        this.audio.load();
        
        this.audio.play().then(() => {
            this.highlightCurrentVerse(verseIndex);
            
            if (this.isMinimized) {
                this.toggleMinimize();
            }
        }).catch(error => {
            console.error('Playback failed:', error);
            const backupUrl = `https://cdn.islamic.network/quran/audio/128/ar.alafasy/${surahNum}${ayahNum}.mp3`;
            this.audio.src = backupUrl;
            this.audio.play();
        });
    }

    updatePlayerInfo(verse) {
        const surahNameEl = document.getElementById('current-surah');
        const ayahInfoEl = document.getElementById('current-ayah');
        
        if (surahNameEl) {
            const surahName = verse.surah_name || `Surah ${verse.surah}`;
            surahNameEl.textContent = `${surahName} - Ayah ${verse.number_in_surah}`;
        }
        
        if (ayahInfoEl) {
            const shortArabic = verse.text_uthmani?.length > 30 
                ? verse.text_uthmani.substring(0, 30) + '...' 
                : verse.text_uthmani || '';
            ayahInfoEl.textContent = shortArabic;
        }
    }

    togglePlay() {
        if (!this.audio.src) {
            if (this.playlist.length > 0) {
                this.playAyah(0);
            }
            return;
        }
        
        if (this.isPlaying) {
            this.audio.pause();
        } else {
            this.audio.play().catch(error => {
                console.error('Playback failed:', error);
                showToast('Cannot play audio. Please try again.', 'error');
            });
        }
    }

    previousAyah() {
        if (this.currentVerseIndex > 0) {
            this.playAyah(this.currentVerseIndex - 1);
        } else {
            showToast('This is the first verse', 'info');
        }
    }

    nextAyah() {
        if (this.currentVerseIndex < this.playlist.length - 1) {
            this.playAyah(this.currentVerseIndex + 1);
        } else if (this.repeatMode) {
            this.playAyah(0);
        } else {
            showToast('This is the last verse', 'info');
        }
    }

    toggleRepeat() {
        this.repeatMode = !this.repeatMode;
        const repeatBtn = document.getElementById('repeat-btn');
        
        if (repeatBtn) {
            repeatBtn.classList.toggle('active', this.repeatMode);
            showToast(this.repeatMode ? 'Repeat: On' : 'Repeat: Off', 'info');
        }
    }

    onPlay() {
        this.isPlaying = true;
        const playBtn = document.getElementById('play-btn');
        const playIcon = document.getElementById('play-icon');
        
        if (playBtn) playBtn.classList.add('playing');
        if (playIcon) playIcon.className = 'fas fa-pause';
    }

    onPause() {
        this.isPlaying = false;
        const playBtn = document.getElementById('play-btn');
        const playIcon = document.getElementById('play-icon');
        
        if (playBtn) playBtn.classList.remove('playing');
        if (playIcon) playIcon.className = 'fas fa-play';
    }

    onAudioEnded() {
        if (this.repeatMode) {
            this.audio.currentTime = 0;
            this.audio.play();
        } else {
            this.nextAyah();
        }
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        this.audio.muted = this.isMuted;
        
        const volumeIcon = document.getElementById('volume-icon');
        if (volumeIcon) {
            volumeIcon.className = this.isMuted ? 'fas fa-volume-mute' : 'fas fa-volume-up';
        }
    }

    toggleSpeed() {
        const speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
        const currentIndex = speeds.indexOf(this.playbackSpeed);
        const nextIndex = (currentIndex + 1) % speeds.length;
        
        this.playbackSpeed = speeds[nextIndex];
        this.audio.playbackRate = this.playbackSpeed;
        
        const speedBtn = document.getElementById('speed-btn');
        if (speedBtn) {
            speedBtn.textContent = `${this.playbackSpeed.toFixed(1)}x`;
        }
        
        showToast(`Speed: ${this.playbackSpeed.toFixed(1)}x`, 'info');
    }

    seekAudio(event) {
        const progressBar = event.currentTarget;
        const rect = progressBar.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const percentage = x / rect.width;
        
        if (this.audio.duration) {
            this.audio.currentTime = percentage * this.audio.duration;
        }
    }

    updateProgress() {
        const progressFill = document.getElementById('progress-fill');
        const currentTime = document.getElementById('current-time');
        
        if (!progressFill || !currentTime) return;
        
        if (this.audio.duration) {
            const percentage = (this.audio.currentTime / this.audio.duration) * 100;
            progressFill.style.width = `${percentage}%`;
            currentTime.textContent = formatTime(this.audio.currentTime);
        }
    }

    updateDuration() {
        const duration = document.getElementById('duration');
        if (duration) {
            duration.textContent = formatTime(this.audio.duration);
        }
    }

    toggleMinimize() {
        const player = document.getElementById('audio-player');
        const icon = document.getElementById('minimize-icon');
        
        if (!player || !icon) return;
        
        this.isMinimized = !this.isMinimized;
        player.classList.toggle('minimized', this.isMinimized);
        
        icon.className = this.isMinimized ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
    }

    highlightCurrentVerse(verseIndex) {
        document.querySelectorAll('.verse').forEach(v => {
            v.classList.remove('playing');
        });
        
        const verseElement = document.querySelector(`.verse[data-index="${verseIndex}"]`);
        if (verseElement) {
            verseElement.classList.add('playing');
            
            const rect = verseElement.getBoundingClientRect();
            if (rect.top < 0 || rect.bottom > window.innerHeight) {
                verseElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }
}

function padNumber(num, length = 3) {
    return num.toString().padStart(length, '0');
}

export default AudioPlayer;