document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const urlInput = document.getElementById('youtube-url');
    const filenameInput = document.getElementById('filename-input');
    const formatSelect = document.getElementById('format-select');
    const qualitySelect = document.getElementById('quality-select');
    const downloadForm = document.getElementById('download-form');
    const startDownloadBtn = document.getElementById('start-download-btn');
    const cancelBtn = document.getElementById('cancel-btn');

    const previewArea = document.getElementById('preview-area');
    const previewImg = document.getElementById('preview-img');
    const previewTitle = document.getElementById('preview-title');
    const optionsArea = document.getElementById('options-area');
    const progressContainer = document.getElementById('progress-container');
    const statusText = document.getElementById('status-text');
    const downloadLinkContainer = document.getElementById('download-link-container');
    const alertContainer = document.getElementById('alert-container');

    const themeToggle = document.getElementById('theme-toggle');

    // --- State ---
    let currentJobId = null;
    let statusInterval = null;
    let mediaInfoCache = null;

    // --- Quality Options ---
    const qualityOptions = {
        video: { 'best': 'Best', '1080p': '1080p', '720p': '720p', '480p': '480p' },
        audio: { 'best': 'Best', 'high': 'High', 'medium': 'Medium', 'low': 'Low' }
    };

    // --- Functions ---
    const showAlert = (message, type = 'error') => {
        const colors = { success: 'bg-green-500', error: 'bg-red-500', info: 'bg-blue-500' };
        const alertDiv = document.createElement('div');
        alertDiv.className = `p-4 text-white rounded-lg shadow-lg mb-2 fade-in ${colors[type]}`;
        alertDiv.textContent = message;
        alertContainer.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    };

    const updateQualityOptions = () => {
        const isAudio = ['mp3', 'wav', 'm4a'].includes(formatSelect.value);
        const options = isAudio ? qualityOptions.audio : qualityOptions.video;
        qualitySelect.innerHTML = '';
        for (const [value, text] of Object.entries(options)) {
            const opt = document.createElement('option');
            opt.value = value;
            opt.textContent = text;
            qualitySelect.appendChild(opt);
        }
    };

    const resetUI = () => {
        previewArea.classList.add('hidden');
        optionsArea.classList.add('hidden');
        progressContainer.classList.add('hidden');
        downloadLinkContainer.innerHTML = '';
        startDownloadBtn.disabled = true;
        filenameInput.value = '';
        mediaInfoCache = null;
        currentJobId = null;
        if (statusInterval) clearInterval(statusInterval);
    };

    const fetchMediaInfo = async (url) => {
        resetUI();
        if (!url) return;

        try {
            const response = await fetch('/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const data = await response.json();

            if (response.status !== 200 || data.error) {
                throw new Error(data.error || 'Failed to fetch media information.');
            }

            mediaInfoCache = data; // Cache the response
            previewTitle.textContent = data.title;
            // Sanitize title for filename
            filenameInput.value = data.title.replace(/[\\/:*?"<>|]/g, '');
            previewImg.src = data.thumbnail || '/static/img/placeholder.png';

            previewArea.classList.remove('hidden');
            optionsArea.classList.remove('hidden');
            startDownloadBtn.disabled = false;

        } catch (error) {
            showAlert(error.message);
            resetUI();
        }
    };

    const pollStatus = async () => {
        if (!currentJobId) return;

        try {
            const response = await fetch(`/status/${currentJobId}`);
            const data = await response.json();

            statusText.textContent = data.message || `Status: ${data.status}`;

            if (data.status === 'completed') {
                clearInterval(statusInterval);
                progressContainer.classList.add('hidden');
                const link = document.createElement('a');
                link.href = data.download_url;
                link.textContent = 'Click here to Download Your File';
                link.className = "theme-button text-white w-full py-3 px-4 rounded-lg font-semibold hover:opacity-90 transition block";
                link.setAttribute('download', '');
                downloadLinkContainer.appendChild(link);
                showAlert('Download complete!', 'success');
            } else if (data.status === 'failed' || data.status === 'cancelled') {
                clearInterval(statusInterval);
                showAlert(`Download failed: ${data.message}`, 'error');
                resetUI();
            }
        } catch (error) {
            clearInterval(statusInterval);
            showAlert('Failed to get download status.', 'error');
            resetUI();
        }
    };

    const handleDownload = async (e) => {
        e.preventDefault();
        if (!mediaInfoCache || !filenameInput.value) {
            showAlert('Please fetch video info and provide a filename first.');
            return;
        }

        startDownloadBtn.disabled = true;
        progressContainer.classList.remove('hidden');
        statusText.textContent = 'Starting download...';

        try {
            const response = await fetch('/start_download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: mediaInfoCache.webpage_url,
                    filename: filenameInput.value,
                    format: formatSelect.value,
                    quality: qualitySelect.value,
                })
            });
            const data = await response.json();

            if (response.status !== 200 || data.error) {
                throw new Error(data.error || 'Failed to start download.');
            }

            currentJobId = data.job_id;
            statusInterval = setInterval(pollStatus, 2000); // Poll every 2 seconds

        } catch (error) {
            showAlert(error.message, 'error');
            resetUI();
        }
    };

    const handleCancel = async () => {
        if (!currentJobId) return;

        try {
            await fetch(`/cancel/${currentJobId}`);
            showAlert('Download cancelled.', 'info');
        } catch (error) {
            showAlert('Failed to cancel download.', 'error');
        } finally {
            clearInterval(statusInterval);
            resetUI();
        }
    };

    const toggleTheme = () => {
        const isDark = document.documentElement.classList.toggle('dark');
        themeToggle.querySelector('.fa-sun').classList.toggle('hidden', isDark);
        themeToggle.querySelector('.fa-moon').classList.toggle('hidden', !isDark);
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    };

    // --- Event Listeners ---
    downloadForm.addEventListener('submit', handleDownload);
    cancelBtn.addEventListener('click', handleCancel);
    formatSelect.addEventListener('change', updateQualityOptions);
    themeToggle.addEventListener('click', toggleTheme);

    let debounceTimer;
    urlInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const url = urlInput.value.trim();
            const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+/;
            if (youtubeRegex.test(url)) {
                fetchMediaInfo(url);
            }
        }, 500); // 500ms debounce
    });

    // --- Initial Setup ---
    if (localStorage.getItem('theme') === 'dark' ||
       (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
    toggleTheme(); toggleTheme(); // Set initial icon state
    updateQualityOptions();
});
