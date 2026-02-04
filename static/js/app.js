// Main application entry point
import CONFIG from './config.js';
import SurahLoader from './surahLoader.js';
import AudioPlayer from './audioPlayer.js';
import BismillahManager from './bismillah.js';
import WordModal from './wordModal.js';
import { showToast } from './utilities.js';

class QuranApp {
    constructor() {
        this.surahLoader = null;
        this.audioPlayer = null;
        this.bismillahManager = null;
        this.wordModal = null;
        this.currentSurahNumber = null;
    }

    async initialize() {
        console.log('Initializing Quran Reader...');
        
        try {
            // Initialize managers
            this.surahLoader = new SurahLoader();
            this.audioPlayer = new AudioPlayer();
            this.bismillahManager = new BismillahManager();
            this.wordModal = new WordModal();
            
            // Load Bismillah data
            await this.bismillahManager.loadBismillah();
            
            // Make available globally
            window.surahLoader = this.surahLoader;
            window.audioPlayer = this.audioPlayer;
            window.bismillahManager = this.bismillahManager;
            window.wordModal = this.wordModal;
            
            // Load surahs list
            await this.surahLoader.loadSurahs();
            
            // Set up event listeners
            this.setupEventListeners();
            this.setupGlobalEventListeners();
            
            // Try to load default surah
            setTimeout(() => this.loadDefaultSurah(), 500);
            
            console.log('Quran Reader initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
            showToast('Failed to initialize application', 'error');
        }
    }

    setupEventListeners() {
        // Surah selector
        const surahSelector = document.getElementById('surah-selector');
        if (surahSelector) {
            surahSelector.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.loadSurahWithBismillah(parseInt(e.target.value));
                }
            });
        }
        
        // Pagination buttons
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const goToBtn = document.getElementById('go-to-btn');
        
        if (prevBtn) prevBtn.addEventListener('click', () => this.surahLoader.prevPage());
        if (nextBtn) nextBtn.addEventListener('click', () => this.surahLoader.nextPage());
        if (goToBtn) goToBtn.addEventListener('click', () => this.surahLoader.goToAyah());
        
        // Go to ayah input
        const goToInput = document.getElementById('go-to-ayah');
        if (goToInput) {
            goToInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.surahLoader.goToAyah();
                }
            });
        }
        
        // Verses per page selector
        const versesPerPageSelect = document.getElementById('verses-per-page');
        if (versesPerPageSelect) {
            versesPerPageSelect.addEventListener('change', (e) => {
                if (this.surahLoader) {
                    this.surahLoader.versesPerPage = parseInt(e.target.value);
                    this.surahLoader.displayPage();
                }
            });
        }
    }

    setupGlobalEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            if (event.target.matches('input, textarea, select')) return;
            
            switch(event.code) {
                case 'Space':
                    event.preventDefault();
                    if (this.audioPlayer) this.audioPlayer.togglePlay();
                    break;
                case 'ArrowLeft':
                    if (event.ctrlKey) {
                        event.preventDefault();
                        if (this.audioPlayer) this.audioPlayer.previousAyah();
                    }
                    break;
                case 'ArrowRight':
                    if (event.ctrlKey) {
                        event.preventDefault();
                        if (this.audioPlayer) this.audioPlayer.nextAyah();
                    }
                    break;
                case 'KeyM':
                    if (event.ctrlKey) {
                        event.preventDefault();
                        if (this.audioPlayer) this.audioPlayer.toggleMute();
                    }
                    break;
                case 'KeyR':
                    if (event.ctrlKey) {
                        event.preventDefault();
                        if (this.audioPlayer) this.audioPlayer.toggleRepeat();
                    }
                    break;
                case 'Escape':
                    if (this.wordModal) this.wordModal.close();
                    break;
            }
        });
        
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.audioPlayer?.isPlaying) {
                this.audioPlayer.audio.pause();
            }
        });
        
        // Topbar scroll effect
        const topbar = document.getElementById("topbar");
        if (topbar) {
            window.addEventListener("scroll", () => {
                if (window.scrollY > 20) {
                    topbar.classList.add("minimized", "scrolled");
                } else {
                    topbar.classList.remove("minimized", "scrolled");
                }
            });
        }
    }

    async loadDefaultSurah() {
        const defaultSurah = CONFIG.DEFAULT_SURAH;
        const surahSelector = document.getElementById('surah-selector');
        
        if (surahSelector) {
            surahSelector.value = defaultSurah.toString();
            await this.loadSurahWithBismillah(defaultSurah);
        }
    }

    async loadSurahWithBismillah(surahNumber) {
        this.currentSurahNumber = surahNumber;
        
        // Load the surah
        await this.surahLoader.loadSurah(surahNumber);
        
        // Handle Bismillah display
        this.handleBismillahDisplay(surahNumber);
    }

    handleBismillahDisplay(surahNumber) {
        const versesContainer = document.getElementById('verses-container');
        if (!versesContainer) return;
        
        // Remove existing Bismillah if any
        const existingBismillah = document.getElementById('bismillah-container');
        if (existingBismillah) existingBismillah.remove();
        
        // Display Bismillah if needed
        if (this.bismillahManager.shouldShowBismillah(surahNumber)) {
            const bismillahContainer = this.bismillahManager.displayBismillah(surahNumber);
            if (bismillahContainer) {
                versesContainer.parentNode.insertBefore(bismillahContainer, versesContainer);
            }
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new QuranApp();
    app.initialize();
    
    // Make app available globally if needed
    window.quranApp = app;
});