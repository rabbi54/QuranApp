// Configuration constants
const CONFIG = {
    VERSES_PER_PAGE: 10,
    DEFAULT_SURAH: 1,
    DEFAULT_RECITER: 'Alafasy',
    QURANWBW_BASE_URL: 'https://words.audios.quranwbw.com',
    EVERY_AYAH_BASE_URL: 'https://everyayah.com/data',
    API_ENDPOINTS: {
        SURAHS: '/api/surahs/',
        SURAH: '/api/surahs/{number}/',
        AYAH_WORD: '/api/verse/{ayahId}/word/{wordIndex}/',
        BISMILLAH: '/api/bismillah/'
    },
    BISMILLAH_AUDIO: {
        Husary: 'https://everyayah.com/data/Husary_128kbps/001001.mp3',
        Basfar: 'https://everyayah.com/data/Abdullah_Basfar_192kbps/001001.mp3',
        Alafasy: 'https://everyayah.com/data/Alafasy_128kbps/001001.mp3'
    }
};

export default CONFIG;