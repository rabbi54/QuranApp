// Utility functions
export function formatTime(seconds) {
    if (isNaN(seconds) || seconds === Infinity) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function padNumber(num, length = 3) {
    return num.toString().padStart(length, '0');
}

export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export function showToast(message, type = 'info') {
    const existingToast = document.querySelector('.toast');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

export function getQuranWBWAudioUrl(surahNumber, ayahNumber, wordIndex) {
    // Adjust for Bismillah in surahs 2-114, first ayah
    let adjustedWordIndex = wordIndex;
    if (surahNumber > 1 && surahNumber !== 9 && ayahNumber === 1) {
        adjustedWordIndex = wordIndex; // Bismillah has 4 words
    }
    
    const surahPadded = padNumber(surahNumber);
    const ayahPadded = padNumber(ayahNumber);
    const wordPadded = padNumber(adjustedWordIndex);
    
    return `https://words.audios.quranwbw.com/${surahNumber}/${surahPadded}_${ayahPadded}_${wordPadded}.mp3`;
}