document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const themeToggle = document.getElementById('theme-toggle');
    const urlInput = document.getElementById('youtube-input'); // Changed from youtube-url
    const formatSelect = document.getElementById('format-select');
    const qualitySelect = document.getElementById('quality-select');
    const qualityContainer = document.getElementById('quality-container');
    const downloadForm = document.getElementById('download-form');
    const downloadBtn = document.getElementById('download-btn');
    const btnText = document.getElementById('btn-text');
    const loader = document.getElementById('loader');
    const thumbnailPreview = document.getElementById('thumbnail-preview');
    const thumbnailImg = document.getElementById('thumbnail-img');
    const videoTitle = document.getElementById('video-title');
    const alertContainer = document.getElementById('alert-container');
    const searchResultsContainer = document.getElementById('search-results');

    // --- Quality Options ---
    const qualityOptions = {
        mp4: ['Best Available', '1080p', '720p', '360p'],
        mp3: ['High', 'Medium', 'Low']
    };

    // --- Functions ---

    /**
     * Toggles between dark and light theme.
     */
    const toggleTheme = () => {
        const html = document.documentElement;
        html.classList.toggle('dark');
        const isDark = html.classList.contains('dark');
        themeToggle.querySelector('.fa-sun').classList.toggle('hidden', isDark);
        themeToggle.querySelector('.fa-moon').classList.toggle('hidden', !isDark);
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    };

    /**
     * Updates the quality dropdown based on the selected format.
     */
    const updateQualityOptions = () => {
        const selectedFormat = formatSelect.value;
        const options = qualityOptions[selectedFormat];

        qualitySelect.innerHTML = ''; // Clear existing options
        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            qualitySelect.appendChild(opt);
        });
    };

    /**
     * Shows an alert message.
     * @param {string} message - The message to display.
     * @param {string} type - 'success', 'error', or 'info'.
     */
    const showAlert = (message, type = 'error') => {
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500'
        };
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
     * Fetches video info and displays thumbnail.
     */
    const fetchVideoInfo = async (url) => {
        try {
            const response = await fetch('/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to fetch video info.');
            }

            const data = await response.json();
            thumbnailImg.src = data.thumbnail;
            videoTitle.textContent = data.title;
            thumbnailPreview.classList.remove('hidden');
            searchResultsContainer.classList.add('hidden'); // Hide search results

        } catch (error) {
            showAlert(error.message);
            thumbnailPreview.classList.add('hidden');
        }
    };

    /**
     * Searches for videos and displays results.
     */
    const searchVideos = async (query) => {
        searchResultsContainer.innerHTML = '<p class="text-center text-gray-500">Searching...</p>';
        searchResultsContainer.classList.remove('hidden');

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.error || 'Failed to perform search.');
            }

            const videos = await response.json();
            displaySearchResults(videos);

        } catch (error) {
            showAlert(error.message);
        }
    };

    /**
     * Displays search results in the UI.
     * @param {Array} videos - An array of video objects.
     */
    const displaySearchResults = (videos) => {
        searchResultsContainer.innerHTML = '';
        if (videos.length === 0) {
            searchResultsContainer.innerHTML = '<p class="text-center text-gray-500">No results found.</p>';
            searchResultsContainer.classList.remove('hidden');
            return;
        }

        videos.forEach(video => {
            const videoElement = document.createElement('div');
            videoElement.className = 'flex items-center p-2 rounded-lg hover:bg-gray-700 cursor-pointer';
            videoElement.innerHTML = `
                <img src="${video.thumbnail}" alt="${video.title}" class="w-16 h-9 object-cover rounded mr-4">
                <span class="text-sm">${video.title}</span>
            `;
            videoElement.addEventListener('click', () => {
                const videoUrl = `https://www.youtube.com/watch?v=${video.id}`;
                urlInput.value = videoUrl;
                fetchVideoInfo(videoUrl);
            });
            searchResultsContainer.appendChild(videoElement);
        });

        searchResultsContainer.classList.remove('hidden');
    };


    /**
     * Handles the form submission for downloading the media.
     */
    const handleDownload = async (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (!url) {
            showAlert('Please paste a YouTube URL or select a video.');
            return;
        }

        btnText.textContent = 'Preparing...';
        loader.classList.remove('hidden');
        downloadBtn.disabled = true;

        const formData = new FormData();
        formData.append('url', url);
        formData.append('format', formatSelect.value);
        formData.append('quality', qualitySelect.value);

        try {
            const response = await fetch('/download', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'An unknown error occurred.');
            }

            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            let filename = 'download';
            if (contentDisposition) {
                 const match = contentDisposition.match(/filename="?(.+?)"?$/);
                 if (match) filename = match[1];
            }

            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(link.href);

            showAlert('Download started successfully!', 'success');

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
            const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/;

            if (youtubeRegex.test(query)) {
                fetchVideoInfo(query);
            } else if (query.length > 2) {
                searchVideos(query);
            } else {
                searchResultsContainer.classList.add('hidden');
                thumbnailPreview.classList.add('hidden');
            }
        }, 1000);
    });

    // --- Initial Setup ---
    if (localStorage.getItem('theme') === 'dark' ||
       (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    themeToggle.querySelector('.fa-sun').classList.toggle('hidden', document.documentElement.classList.contains('dark'));
    themeToggle.querySelector('.fa-moon').classList.toggle('hidden', !document.documentElement.classList.contains('dark'));

    updateQualityOptions();
});