// ============ File Management ============
let selectedFiles = [];

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');

// Usuń required - sami zarządzamy walidacją
if (fileInput) {
    fileInput.removeAttribute('required');
}

if (dropZone && fileInput) {
    dropZone.addEventListener('click', (e) => {
        if (e.target.closest('.file-list') || e.target.closest('.file-remove')) {
            return;
        }
        fileInput.click();
    });
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        addFiles(e.dataTransfer.files);
    });
    
    fileInput.addEventListener('change', () => {
        addFiles(fileInput.files);
        fileInput.value = '';
    });
    
    fileList.addEventListener('click', (e) => {
        const removeBtn = e.target.closest('.file-remove');
        if (removeBtn) {
            e.preventDefault();
            e.stopPropagation();
            const index = parseInt(removeBtn.dataset.index);
            removeFile(index);
        }
    });
}

function addFiles(files) {
    for (const file of files) {
        const exists = selectedFiles.some(f => f.name === file.name && f.size === file.size);
        if (!exists) {
            selectedFiles.push(file);
        }
    }
    updateFileList();
    updateFileInput();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateFileInput();
}

function updateFileList() {
    if (!fileList) return;
    
    fileList.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <svg class="file-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18V5l12-2v13"/>
                <circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
            </svg>
            <span class="file-name">${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
            <button type="button" class="file-remove" data-index="${index}" title="Remove file">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        `;
        fileList.appendChild(div);
    });
}

function updateFileInput() {
    if (!fileInput) return;
    
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach(file => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// ============ Form Submit ============
const form = document.getElementById('uploadForm');
const submitBtn = document.getElementById('submitBtn');
const loadingOverlay = document.getElementById('loadingOverlay');

form?.addEventListener('submit', (e) => {
    if (selectedFiles.length === 0) {
        e.preventDefault();
        alert('Please select at least one file.');
        return;
    }
    
    updateFileInput();
    
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    loadingOverlay?.classList.add('active');
});

// ============ Audio Player ============
function initAudioPlayers() {
    document.querySelectorAll('.play-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const audioId = btn.dataset.audio;
            const audio = document.getElementById(audioId);
            const iconPlay = btn.querySelector('.icon-play');
            const iconPause = btn.querySelector('.icon-pause');
            
            if (audio.paused) {
                // Pause all other audio
                document.querySelectorAll('audio').forEach(a => {
                    if (a !== audio) {
                        a.pause();
                        const otherBtn = document.querySelector(`.play-btn[data-audio="${a.id}"]`);
                        if (otherBtn) {
                            otherBtn.querySelector('.icon-play').style.display = 'block';
                            otherBtn.querySelector('.icon-pause').style.display = 'none';
                        }
                    }
                });
                audio.play();
                iconPlay.style.display = 'none';
                iconPause.style.display = 'block';
            } else {
                audio.pause();
                iconPlay.style.display = 'block';
                iconPause.style.display = 'none';
            }
        });
    });

    // Progress bars
    document.querySelectorAll('audio').forEach(audio => {
        const progressBar = document.querySelector(`.progress-bar[data-audio="${audio.id}"]`);
        const progressFill = progressBar?.querySelector('.progress-fill');
        const timeDisplay = document.querySelector(`.player-time[data-audio="${audio.id}"]`);
        
        audio.addEventListener('timeupdate', () => {
            if (progressFill) {
                const percent = (audio.currentTime / audio.duration) * 100;
                progressFill.style.width = `${percent}%`;
            }
            if (timeDisplay) {
                timeDisplay.textContent = `${formatTime(audio.currentTime)} / ${formatTime(audio.duration)}`;
            }
        });
        
        audio.addEventListener('ended', () => {
            const btn = document.querySelector(`.play-btn[data-audio="${audio.id}"]`);
            if (btn) {
                btn.querySelector('.icon-play').style.display = 'block';
                btn.querySelector('.icon-pause').style.display = 'none';
            }
        });
        
        progressBar?.addEventListener('click', (e) => {
            const rect = progressBar.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            audio.currentTime = percent * audio.duration;
        });
    });

    // Volume controls
    document.querySelectorAll('.volume-slider').forEach(slider => {
        const audioId = slider.dataset.audio;
        const audio = document.getElementById(audioId);
        const volumeBtn = document.querySelector(`.volume-btn[data-audio="${audioId}"]`);
        
        slider.addEventListener('input', () => {
            const value = parseFloat(slider.value);
            audio.volume = value;
            updateVolumeIcon(volumeBtn, value);
        });
        
        volumeBtn?.addEventListener('click', () => {
            if (audio.muted) {
                audio.muted = false;
                slider.value = audio.volume || 1;
                updateVolumeIcon(volumeBtn, audio.volume);
            } else {
                audio.muted = true;
                updateVolumeIcon(volumeBtn, 0);
            }
        });
    });
}

function updateVolumeIcon(btn, volume) {
    if (!btn) return;
    
    const iconHigh = btn.querySelector('.icon-volume-high');
    const iconLow = btn.querySelector('.icon-volume-low');
    const iconMute = btn.querySelector('.icon-volume-mute');
    
    iconHigh.style.display = 'none';
    iconLow.style.display = 'none';
    iconMute.style.display = 'none';
    
    if (volume === 0) {
        iconMute.style.display = 'block';
    } else if (volume < 0.5) {
        iconLow.style.display = 'block';
    } else {
        iconHigh.style.display = 'block';
    }
}

function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============ Copy to Clipboard ============
function initCopyButtons() {
    document.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', async () => {
            const targetId = btn.dataset.target;
            const text = document.getElementById(targetId)?.textContent;
            
            try {
                await navigator.clipboard.writeText(text);
                const iconCopy = btn.querySelector('.icon-copy');
                const iconCheck = btn.querySelector('.icon-check');
                
                iconCopy.style.display = 'none';
                iconCheck.style.display = 'block';
                btn.classList.add('copied');
                
                setTimeout(() => {
                    iconCopy.style.display = 'block';
                    iconCheck.style.display = 'none';
                    btn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    });
}

// ============ Initialize ============
initAudioPlayers();
initCopyButtons();