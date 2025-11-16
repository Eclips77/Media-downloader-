document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const themeToggle = document.getElementById('theme-toggle');
    const urlInput = document.getElementById('youtube-input');
    const formatSelect = document.getElementById('format-select');
    const qualitySelect = document.getElementById('quality-select');
    const downloadForm = document.getElementById('download-form');
    const downloadBtn = document.getElementById('download-btn');
    const btnText = document.getElementById('btn-text');
    const loader = document.getElementById('loader');
    const previewArea = document.getElementById('preview-area');
    const previewImg = document.getElementById('preview-img');
    const previewTitle = document.getElementById('preview-title');
    const alertContainer = document.getElementById('alert-container');
    const searchResultsContainer = document.getElementById('search-results');
    const downloadLinksContainer = document.getElementById('download-links');

    // --- State ---
    let selectedMedia = null; // To store info about the selected video or playlist

    // --- Quality Options ---
    const qualityOptions = {
        video: ['Best', '1080p', '720p', '480p'],
        audio: ['High', 'Medium', 'Low']
    };

    // --- Functions ---

    /**
     * Toggles between dark and light theme.
     */
    const toggleTheme = () => {
        document.documentElement.classList.toggle('dark');
        const isDark = document.documentElement.classList.contains('dark');
        themeToggle.querySelector('.fa-sun').classList.toggle('hidden', isDark);
        themeToggle.querySelector('.fa-moon').classList.toggle('hidden', !isDark);
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    };

    /**
     * Updates the quality dropdown based on the selected format.
     */
    const updateQualityOptions = () => {
        const formatValue = formatSelect.value;
        const formatType = ['mp3', 'wav', 'm4a'].includes(formatValue) ? 'audio' : 'video';
        const options = qualityOptions[formatType];

        qualitySelect.innerHTML = '';
        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option.toLowerCase();
            opt.textContent = option;
            qualitySelect.appendChild(opt);
        });
    };

    /**
     * Shows an alert message.
     */
    const showAlert = (message, type = 'error') => {
        const colors = { success: 'bg-green-500', error: 'bg-red-500', info: 'bg-blue-500' };
        const alertDiv = document.createElement('div');
        alertDiv.className = `p-4 text-white rounded-lg shadow-lg mb-2 fade-in ${colors[type]}`;
        alertDiv.textContent = message;
        alertContainer.appendChild(alertDiv);
        setTimeout(() => {
            alertDiv.classList.add('fade-out');
            alertDiv.addEventListener('animationend', () => alertDiv.remove());
        }, 5000);
    };

    /**
     * Resets the UI to its initial state.
     */
    const resetUI = () => {
        previewArea.classList.add('hidden');
        searchResultsContainer.classList.add('hidden');
        searchResultsContainer.innerHTML = '';
        downloadLinksContainer.innerHTML = '';
        selectedMedia = null;
    };

    /**
     * Fetches media info (video or playlist) and updates the UI.
     */
    const fetchMediaInfo = async (url) => {
        resetUI();
        try {
            const response = await fetch('/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to fetch media info.');
            }

            const data = await response.json();
            selectedMedia = { ...data, url }; // Store the info

            previewTitle.textContent = data.title;
            if (data.type === 'playlist') {
                previewImg.src = "https://i.imgur.com/3h2tS2A.png"; // Generic playlist icon
                previewTitle.textContent = `Playlist: ${data.title}`;
            } else {
                previewImg.src = data.thumbnail;
            }
            previewArea.classList.remove('hidden');

        } catch (error) {
            showAlert(error.message);
            resetUI();
        }
    };

    /**
     * Searches for videos and displays results.
     */
    const searchVideos = async (query) => {
        resetUI();
        searchResultsContainer.innerHTML = '<p class="text-center text-gray-400">Searching...</p>';
        searchResultsContainer.classList.remove('hidden');

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            if (!response.ok) throw new Error('Search failed.');

            const videos = await response.json();
            displaySearchResults(videos);

        } catch (error) {
            showAlert(error.message);
        }
    };

    /**
     * Displays search results in the UI.
     */
    const displaySearchResults = (videos) => {
        searchResultsContainer.innerHTML = '';
        if (!videos || videos.length === 0) {
            searchResultsContainer.innerHTML = '<p class="text-center text-gray-400">No results found.</p>';
            return;
        }

        videos.forEach(video => {
            const videoElement = document.createElement('div');
            videoElement.className = 'theme-card flex items-center p-2 rounded-lg hover:bg-opacity-70 cursor-pointer fade-in border';
            videoElement.innerHTML = `
                <img src="${video.thumbnail}" alt="${video.title}" class="w-24 h-14 object-cover rounded mr-4">
                <div>
                    <span class="font-semibold">${video.title}</span>
                    <span class="text-sm text-gray-400 block">${video.uploader || ''}</span>
                </div>
            `;
            videoElement.addEventListener('click', () => {
                urlInput.value = video.webpage_url;
                fetchMediaInfo(video.webpage_url);
            });
            searchResultsContainer.appendChild(videoElement);
        });
    };

    /**
     * Handles the form submission to initiate a download.
     */
    const handleDownload = async (e) => {
        e.preventDefault();
        if (!selectedMedia || !selectedMedia.url) {
            showAlert('Please select a video or playlist first.');
            return;
        }

        btnText.textContent = 'Downloading to Server...';
        loader.classList.remove('hidden');
        downloadBtn.disabled = true;
        downloadLinksContainer.innerHTML = '';

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: selectedMedia.url,
                    format: formatSelect.value,
                    quality: qualitySelect.value,
                    is_playlist: selectedMedia.type === 'playlist'
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'An unknown error occurred during download.');
            }

            const result = await response.json();
            if (result.status === 'success') {
                const link = document.createElement('a');
                link.href = result.download_url;
                link.textContent = `Download "${result.filename}"`;
                link.className = "theme-button text-white w-full py-2 px-4 rounded-lg font-semibold hover:opacity-90 transition block";
                link.setAttribute('download', '');
                downloadLinksContainer.appendChild(link);
                showAlert('File is ready for download!', 'success');
            } else {
                throw new Error(result.message);
            }

        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            btnText.textContent = 'Download';
            loader.classList.add('hidden');
            downloadBtn.disabled = false;
        }
    };

    // --- Event Listeners ---
    themeToggle.addEventListener('click', toggleTheme);
    formatSelect.addEventListener('change', updateQualityOptions);
    downloadForm.addEventListener('submit', handleDownload);

    let debounceTimer;
    urlInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = urlInput.value.trim();
            const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/(watch\?v=.+|playlist\?list=.+|.+)/;

            if (youtubeRegex.test(query)) {
                fetchMediaInfo(query);
            } else if (query.length > 2) {
                searchVideos(query);
            } else {
                resetUI();
            }
        }, 800);
    });

    // --- Initial Setup ---
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && prefersDark)) {
        document.documentElement.classList.add('dark');
    }
    themeToggle.querySelector('.fa-sun').classList.toggle('hidden', document.documentElement.classList.contains('dark'));
    themeToggle.querySelector('.fa-moon').classList.toggle('hidden', !document.documentElement.classList.contains('dark'));
    updateQualityOptions();
});