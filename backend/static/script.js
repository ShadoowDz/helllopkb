// Global variables
let currentJobId = null;
let progressInterval = null;
let selectedFile = null;

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const optionsPanel = document.getElementById('optionsPanel');
const convertBtn = document.getElementById('convertBtn');
const uploadSection = document.getElementById('uploadSection');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const currentStep = document.getElementById('currentStep');
const logOutput = document.getElementById('logOutput');
const jobIdDisplay = document.getElementById('jobIdDisplay');
const downloadBtn = document.getElementById('downloadBtn');
const cancelBtn = document.getElementById('cancelBtn');
const retryBtn = document.getElementById('retryBtn');
const successResults = document.getElementById('successResults');
const errorResults = document.getElementById('errorResults');
const errorMessage = document.getElementById('errorMessage');
const errorLog = document.getElementById('errorLog');
const loadingOverlay = document.getElementById('loadingOverlay');
const modal = document.getElementById('modal');
const modalContent = document.getElementById('modalContent');

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    resetInterface();
}

function setupEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop events
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Button events
    convertBtn.addEventListener('click', startConversion);
    cancelBtn.addEventListener('click', cancelConversion);
    retryBtn.addEventListener('click', resetInterface);
    downloadBtn.addEventListener('click', downloadResults);
    
    // Prevent default drag behavior on document
    document.addEventListener('dragover', (e) => e.preventDefault());
    document.addEventListener('drop', (e) => e.preventDefault());
}

// File handling
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        validateAndSetFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        validateAndSetFile(files[0]);
    }
}

function validateAndSetFile(file) {
    // Validate file type
    const allowedTypes = ['.fbx', '.FBX'];
    const fileExtension = '.' + file.name.split('.').pop();
    
    if (!allowedTypes.includes(fileExtension)) {
        showError('Please select a valid FBX file.');
        return;
    }
    
    // Validate file size (100MB)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('File size must be less than 100MB.');
        return;
    }
    
    if (file.size < 1024) {
        showError('File is too small to be a valid FBX file.');
        return;
    }
    
    selectedFile = file;
    displaySelectedFile(file);
    showOptionsPanel();
}

function displaySelectedFile(file) {
    const uploadIcon = uploadArea.querySelector('.upload-icon i');
    const uploadTitle = uploadArea.querySelector('h3');
    const uploadDesc = uploadArea.querySelector('p');
    
    uploadIcon.className = 'fas fa-file-3d';
    uploadTitle.textContent = 'FBX File Selected';
    uploadDesc.innerHTML = `
        <strong>${file.name}</strong><br>
        Size: ${formatFileSize(file.size)}<br>
        <span class="file-info">Ready for conversion</span>
    `;
}

function showOptionsPanel() {
    optionsPanel.style.display = 'block';
    optionsPanel.classList.add('fade-in');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Conversion process
async function startConversion() {
    if (!selectedFile) {
        showError('Please select a file first.');
        return;
    }
    
    const scale = document.getElementById('scaleInput').value;
    const bodygroupName = document.getElementById('bodygroupInput').value;
    
    // Validate inputs
    if (!scale || scale <= 0 || scale > 100) {
        showError('Please enter a valid scale between 0.1 and 100.');
        return;
    }
    
    if (!bodygroupName || bodygroupName.trim().length === 0) {
        showError('Please enter a valid bodygroup name.');
        return;
    }
    
    showLoadingOverlay('Uploading file...');
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('scale', scale);
        formData.append('bodygroup_name', bodygroupName.trim());
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        hideLoadingOverlay();
        
        if (response.ok) {
            currentJobId = result.job_id;
            showProgressSection();
            startProgressTracking();
        } else {
            showError(result.error || 'Upload failed. Please try again.');
        }
        
    } catch (error) {
        hideLoadingOverlay();
        showError('Network error. Please check your connection and try again.');
        console.error('Upload error:', error);
    }
}

function showProgressSection() {
    uploadSection.style.display = 'none';
    progressSection.style.display = 'block';
    progressSection.classList.add('fade-in');
    resultsSection.style.display = 'none';
    
    jobIdDisplay.textContent = `Job ID: ${currentJobId}`;
    updateProgress(0, 'Starting conversion...');
    clearLog();
}

function startProgressTracking() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${currentJobId}`);
            const status = await response.json();
            
            if (response.ok) {
                updateProgress(status.progress, status.log[status.log.length - 1] || 'Processing...');
                updateLog(status.log);
                
                if (status.status === 'completed') {
                    clearInterval(progressInterval);
                    showSuccessResults();
                } else if (status.status === 'failed') {
                    clearInterval(progressInterval);
                    showErrorResults(status.error);
                }
            } else {
                clearInterval(progressInterval);
                showErrorResults(status.error || 'Failed to get job status');
            }
            
        } catch (error) {
            console.error('Status check error:', error);
            // Continue checking, might be temporary network issue
        }
    }, 2000); // Check every 2 seconds
}

function updateProgress(progress, step) {
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    currentStep.textContent = step;
}

function updateLog(logEntries) {
    // Only update if we have new entries
    const currentLogCount = logOutput.children.length;
    if (logEntries.length > currentLogCount) {
        // Add new entries
        for (let i = currentLogCount; i < logEntries.length; i++) {
            const logEntry = document.createElement('p');
            logEntry.className = 'log-entry';
            logEntry.textContent = logEntries[i];
            logOutput.appendChild(logEntry);
        }
        
        // Auto-scroll to bottom
        logOutput.scrollTop = logOutput.scrollHeight;
    }
}

function clearLog() {
    logOutput.innerHTML = '<p class="log-entry">Conversion started...</p>';
}

function cancelConversion() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    showConfirmDialog(
        'Cancel Conversion',
        'Are you sure you want to cancel the conversion? This action cannot be undone.',
        () => {
            resetInterface();
        }
    );
}

function showSuccessResults() {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    successResults.style.display = 'block';
    errorResults.style.display = 'none';
}

function showErrorResults(error) {
    progressSection.style.display = 'none';
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    successResults.style.display = 'none';
    errorResults.style.display = 'block';
    
    errorMessage.textContent = error || 'An unknown error occurred during conversion.';
    
    // Show log if available
    const logEntries = Array.from(logOutput.children).map(entry => entry.textContent);
    if (logEntries.length > 0) {
        errorLog.textContent = logEntries.join('\n');
        errorLog.style.display = 'block';
    } else {
        errorLog.style.display = 'none';
    }
}

async function downloadResults() {
    if (!currentJobId) {
        showError('No conversion results available.');
        return;
    }
    
    try {
        showLoadingOverlay('Preparing download...');
        
        const response = await fetch(`/download/${currentJobId}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `converted_model_${currentJobId}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            hideLoadingOverlay();
            showSuccess('Download started successfully!');
        } else {
            const error = await response.json();
            hideLoadingOverlay();
            showError(error.error || 'Download failed. Please try again.');
        }
        
    } catch (error) {
        hideLoadingOverlay();
        showError('Network error during download. Please try again.');
        console.error('Download error:', error);
    }
}

function resetInterface() {
    // Clear intervals
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    
    // Reset variables
    currentJobId = null;
    selectedFile = null;
    
    // Reset file input
    fileInput.value = '';
    
    // Reset sections
    uploadSection.style.display = 'block';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    optionsPanel.style.display = 'none';
    
    // Reset upload area
    const uploadIcon = uploadArea.querySelector('.upload-icon i');
    const uploadTitle = uploadArea.querySelector('h3');
    const uploadDesc = uploadArea.querySelector('p');
    
    uploadIcon.className = 'fas fa-cloud-upload-alt';
    uploadTitle.textContent = 'Upload your FBX model';
    uploadDesc.innerHTML = 'Drag and drop your .fbx file here, or click to browse<br><span class="file-info">Maximum file size: 100MB</span>';
    
    // Reset form values
    document.getElementById('scaleInput').value = '1.0';
    document.getElementById('bodygroupInput').value = 'default';
    
    uploadArea.classList.remove('dragover');
    hideLoadingOverlay();
    closeModal();
}

// UI Helper functions
function showLoadingOverlay(message = 'Processing...') {
    loadingOverlay.style.display = 'flex';
    loadingOverlay.querySelector('p').textContent = message;
}

function hideLoadingOverlay() {
    loadingOverlay.style.display = 'none';
}

function showError(message) {
    showNotification(message, 'error');
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'error' ? 'fa-exclamation-triangle' : type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? 'var(--error-color)' : type === 'success' ? 'var(--success-color)' : 'var(--primary-color)'};
        color: white;
        padding: 1rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-lg);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.querySelector('button').style.cssText = `
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 0.25rem;
        margin-left: auto;
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function showConfirmDialog(title, message, onConfirm) {
    modalContent.innerHTML = `
        <h3>${title}</h3>
        <p style="margin: 1rem 0;">${message}</p>
        <div style="display: flex; gap: 1rem; justify-content: flex-end;">
            <button onclick="closeModal()" style="padding: 0.5rem 1rem; border: 1px solid var(--border-color); background: var(--surface-color); border-radius: var(--border-radius); cursor: pointer;">
                Cancel
            </button>
            <button onclick="closeModal(); (${onConfirm.toString()})()" style="padding: 0.5rem 1rem; background: var(--error-color); color: white; border: none; border-radius: var(--border-radius); cursor: pointer;">
                Confirm
            </button>
        </div>
    `;
    modal.style.display = 'flex';
}

function closeModal() {
    modal.style.display = 'none';
}

// Footer functions
async function showHealthStatus() {
    showLoadingOverlay('Checking server status...');
    
    try {
        const response = await fetch('/health');
        const health = await response.json();
        
        hideLoadingOverlay();
        
        modalContent.innerHTML = `
            <h3><i class="fas fa-heartbeat"></i> Server Health Status</h3>
            <div style="margin: 1rem 0;">
                <p><strong>Status:</strong> ${health.status}</p>
                <p><strong>Active Jobs:</strong> ${health.active_jobs}</p>
                <p><strong>Total Jobs:</strong> ${health.total_jobs}</p>
                <p><strong>Last Check:</strong> ${new Date().toLocaleString()}</p>
            </div>
            <div style="padding: 1rem; background: var(--background-color); border-radius: var(--border-radius); margin: 1rem 0;">
                <h4>System Requirements:</h4>
                <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                    <li>Blender (headless mode)</li>
                    <li>Wine (for studiomdl.exe)</li>
                    <li>GoldSrc SDK Tools</li>
                </ul>
            </div>
        `;
        modal.style.display = 'flex';
        
    } catch (error) {
        hideLoadingOverlay();
        showError('Failed to get server status.');
    }
}

function showAbout() {
    modalContent.innerHTML = `
        <h3><i class="fas fa-info-circle"></i> About FBX to MDL Converter</h3>
        <div style="margin: 1rem 0; line-height: 1.6;">
            <p>This application converts FBX 3D models to MDL format compatible with the GoldSrc engine used in Counter-Strike 1.6.</p>
            
            <h4 style="margin-top: 1.5rem;">Conversion Pipeline:</h4>
            <ol style="margin: 0.5rem 0; padding-left: 1.5rem;">
                <li>FBX file upload and validation</li>
                <li>Blender converts FBX to SMD format</li>
                <li>QC file generation with GoldSrc settings</li>
                <li>studiomdl.exe compiles MDL from SMD + QC</li>
                <li>Result packaging and download</li>
            </ol>
            
            <h4 style="margin-top: 1.5rem;">Features:</h4>
            <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                <li>Automatic mesh and animation conversion</li>
                <li>GoldSrc compatibility optimizations</li>
                <li>Real-time progress tracking</li>
                <li>Comprehensive error logging</li>
                <li>Secure file validation</li>
                <li>Rate limiting protection</li>
            </ul>
            
            <h4 style="margin-top: 1.5rem;">Technical Stack:</h4>
            <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
                <li>Backend: Python Flask</li>
                <li>3D Processing: Blender + Source Tools</li>
                <li>Compilation: GoldSrc SDK studiomdl.exe</li>
                <li>Frontend: Modern HTML5/CSS3/JavaScript</li>
            </ul>
            
            <p style="margin-top: 1.5rem; font-size: 0.875rem; color: var(--text-muted);">
                Built for the Counter-Strike 1.6 modding community. Ensure your models comply with GoldSrc engine limitations for best results.
            </p>
        </div>
    `;
    modal.style.display = 'flex';
}

// Click outside modal to close
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        closeModal();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape key to close modal or cancel operation
    if (e.key === 'Escape') {
        if (modal.style.display === 'flex') {
            closeModal();
        } else if (progressSection.style.display === 'block') {
            cancelConversion();
        }
    }
    
    // Ctrl+R to reset (prevent default browser refresh)
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        resetInterface();
    }
});

// Add notification styles to document
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .notification {
        animation: slideIn 0.3s ease-out;
    }
`;
document.head.appendChild(notificationStyles);