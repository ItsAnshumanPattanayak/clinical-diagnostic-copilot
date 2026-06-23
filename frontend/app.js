/**
 * Clinical Diagnostic Copilot - Frontend JavaScript
 * ==================================================
 * Handles all client-side interactions:
 * - File upload and validation
 * - Drag & drop
 * - API communication
 * - UI updates
 * 
 * Uses vanilla JavaScript (no frameworks) for simplicity and performance.
 */

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const AppState = {
    selectedFile: null,
    isProcessing: false,
    currentStep: 0
};

// ============================================================================
// DOM ELEMENT REFERENCES
// ============================================================================

const elements = {
    // Sections
    uploadSection: document.getElementById('uploadSection'),
    previewSection: document.getElementById('previewSection'),
    loadingSection: document.getElementById('loadingSection'),
    resultsSection: document.getElementById('resultsSection'),
    errorSection: document.getElementById('errorSection'),
    
    // Upload
    imageInput: document.getElementById('imageInput'),
    uploadBtn: document.getElementById('uploadBtn'),
    dropZone: document.getElementById('dropZone'),
    
    // Preview
    imagePreview: document.getElementById('imagePreview'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    cancelBtn: document.getElementById('cancelBtn'),
    
    // Loading
    loadingMessage: document.getElementById('loadingMessage'),
    step1: document.getElementById('step1'),
    step2: document.getElementById('step2'),
    step3: document.getElementById('step3'),
    
    // Results
    diagnosisName: document.getElementById('diagnosisName'),
    confidenceBadge: document.getElementById('confidenceBadge'),
    confidenceFill: document.getElementById('confidenceFill'),
    reviewFlag: document.getElementById('reviewFlag'),
    predictionsList: document.getElementById('predictionsList'),
    researchContent: document.getElementById('researchContent'),
    reportContent: document.getElementById('reportContent'),
    downloadBtn: document.getElementById('downloadBtn'),
    newAnalysisBtn: document.getElementById('newAnalysisBtn'),
    
    // Error
    errorMessage: document.getElementById('errorMessage'),
    retryBtn: document.getElementById('retryBtn'),
    
    // Status
    statusBadge: document.getElementById('statusBadge'),
    statusText: document.getElementById('statusText')
};

// ============================================================================
// INITIALIZATION
// ============================================================================

function init() {
    console.log('🚀 Initializing Clinical Diagnostic Copilot...');
    
    // Attach event listeners
    attachEventListeners();
    
    // Check server health
    checkServerHealth();
    
    console.log('✅ Frontend initialized');
}

function attachEventListeners() {
    // Upload button
    elements.uploadBtn.addEventListener('click', () => {
        elements.imageInput.click();
    });
    
    // File input change
    elements.imageInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    elements.dropZone.addEventListener('dragover', handleDragOver);
    elements.dropZone.addEventListener('dragleave', handleDragLeave);
    elements.dropZone.addEventListener('drop', handleDrop);
    
    // Preview buttons
    elements.analyzeBtn.addEventListener('click', analyzeImage);
    elements.cancelBtn.addEventListener('click', resetToUpload);
    
    // Results buttons
    elements.downloadBtn.addEventListener('click', downloadReport);
    elements.newAnalysisBtn.addEventListener('click', resetToUpload);
    
    // Error button
    elements.retryBtn.addEventListener('click', resetToUpload);
}

// ============================================================================
// SERVER HEALTH CHECK
// ============================================================================

async function checkServerHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateStatus('System Ready', 'success');
            console.log('✅ Server health check passed');
        } else {
            updateStatus('System Degraded', 'warning');
        }
    } catch (error) {
        updateStatus('Server Offline', 'error');
        console.error('❌ Health check failed:', error);
    }
}

function updateStatus(text, status) {
    elements.statusText.textContent = text;
    
    const statusDot = elements.statusBadge.querySelector('.status-dot');
    statusDot.style.background = {
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444'
    }[status] || '#6b7280';
}

// ============================================================================
// FILE HANDLING
// ============================================================================

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        validateAndPreviewFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    elements.dropZone.classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    elements.dropZone.classList.remove('drag-over');
}

function handleDrop(event) {
    event.preventDefault();
    elements.dropZone.classList.remove('drag-over');
    
    const file = event.dataTransfer.files[0];
    if (file) {
        validateAndPreviewFile(file);
    }
}

function validateAndPreviewFile(file) {
    console.log('📁 File selected:', file.name);
    
    // Validate file type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload a JPG, PNG, BMP, or TIFF image.');
        return;
    }
    
    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showError('File too large. Maximum size is 10MB.');
        return;
    }
    
    // Store file in state
    AppState.selectedFile = file;
    
    // Show preview
    showPreview(file);
}

function showPreview(file) {
    // Read file as data URL for preview
    const reader = new FileReader();
    
    reader.onload = (e) => {
        elements.imagePreview.src = e.target.result;
        elements.fileName.textContent = file.name;
        elements.fileSize.textContent = formatFileSize(file.size);
        
        // Show preview section, hide upload section
        showSection('preview');
    };
    
    reader.readAsDataURL(file);
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// ============================================================================
// IMAGE ANALYSIS
// ============================================================================

async function analyzeImage() {
    if (!AppState.selectedFile) {
        showError('No file selected');
        return;
    }
    
    if (AppState.isProcessing) {
        console.warn('⚠️ Analysis already in progress');
        return;
    }
    
    AppState.isProcessing = true;
    showSection('loading');
    updateStatus('Processing...', 'warning');
    
    // Simulate progress through steps
    simulateProgress();
    
    try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('image', AppState.selectedFile);
        
        console.log('🔬 Sending image for analysis...');
        
        // Send POST request to backend
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        
        // Parse JSON response
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Analysis failed');
        }
        
        if (!data.success) {
            throw new Error(data.error || 'Unknown error occurred');
        }
        
        console.log('✅ Analysis complete:', data);
        
        // Display results
        displayResults(data);
        
        updateStatus('Analysis Complete', 'success');
        
    } catch (error) {
        console.error('❌ Analysis error:', error);
        showError(error.message);
        updateStatus('Analysis Failed', 'error');
    } finally {
        AppState.isProcessing = false;
    }
}

function simulateProgress() {
    // Simulate agent workflow steps
    const steps = [elements.step1, elements.step2, elements.step3];
    const messages = [
        'Running vision analysis...',
        'Searching medical literature...',
        'Generating diagnostic report...'
    ];
    
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep < steps.length && AppState.isProcessing) {
            steps[currentStep].classList.add('active');
            elements.loadingMessage.textContent = messages[currentStep];
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 1500);
}

// ============================================================================
// RESULTS DISPLAY
// ============================================================================

function displayResults(data) {
    // Primary diagnosis
    elements.diagnosisName.textContent = data.primary_diagnosis || 'Unknown';
    
    const confidence = data.confidence || 0;
    elements.confidenceBadge.textContent = `${(confidence * 100).toFixed(1)}% confidence`;
    elements.confidenceFill.style.width = `${confidence * 100}%`;
    
    // Review flag
    if (data.requires_review) {
        elements.reviewFlag.classList.remove('hidden');
    } else {
        elements.reviewFlag.classList.add('hidden');
    }
    
    // All predictions
    displayPredictions(data.all_predictions || []);
    
    // Research summary
    elements.researchContent.textContent = data.research_summary || 'No research data available.';
    
    // Final report
    elements.reportContent.textContent = data.final_report || 'No report generated.';
    
    // Store report for download
    AppState.currentReport = data.final_report;
    
    // Show results section
    showSection('results');
}

function displayPredictions(predictions) {
    elements.predictionsList.innerHTML = '';
    
    predictions.forEach((pred, index) => {
        const item = document.createElement('div');
        item.className = 'prediction-item';
        
        const leftSide = document.createElement('div');
        leftSide.innerHTML = `
            <span class="prediction-name">${pred.condition}</span>
            <span class="severity-badge severity-${pred.severity}">${pred.severity}</span>
        `;
        
        const rightSide = document.createElement('div');
        rightSide.className = 'prediction-confidence';
        rightSide.textContent = `${(pred.confidence * 100).toFixed(1)}%`;
        
        item.appendChild(leftSide);
        item.appendChild(rightSide);
        
        elements.predictionsList.appendChild(item);
    });
}

// ============================================================================
// REPORT DOWNLOAD
// ============================================================================

function downloadReport() {
    const report = AppState.currentReport || 'No report available';
    const filename = `diagnostic_report_${new Date().toISOString().slice(0, 10)}.txt`;
    
    // Create blob and download link
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    
    URL.revokeObjectURL(url);
    
    console.log('💾 Report downloaded:', filename);
}

// ============================================================================
// UI STATE MANAGEMENT
// ============================================================================

function showSection(sectionName) {
    // Hide all sections
    const sections = ['upload', 'preview', 'loading', 'results', 'error'];
    sections.forEach(name => {
        const element = elements[`${name}Section`];
        if (element) {
            element.classList.add('hidden');
        }
    });
    
    // Show requested section
    const targetSection = elements[`${sectionName}Section`];
    if (targetSection) {
        targetSection.classList.remove('hidden');
    }
    
    // Reset loading steps
    if (sectionName !== 'loading') {
        [elements.step1, elements.step2, elements.step3].forEach(step => {
            step.classList.remove('active');
        });
    }
}

function showError(message) {
    elements.errorMessage.textContent = message;
    showSection('error');
}

function resetToUpload() {
    // Clear state
    AppState.selectedFile = null;
    AppState.isProcessing = false;
    AppState.currentReport = null;
    
    // Reset file input
    elements.imageInput.value = '';
    
    // Show upload section
    showSection('upload');
    
    // Reset status
    updateStatus('System Ready', 'success');
}

// ============================================================================
// START APPLICATION
// ============================================================================

// Wait for DOM to be fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}