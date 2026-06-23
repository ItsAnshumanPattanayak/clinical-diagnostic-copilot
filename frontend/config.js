/**
 * Frontend Configuration
 * This file manages API endpoint URLs for different environments
 */

// Detect environment
const isProduction = window.location.hostname !== 'localhost';

// API Configuration
const API_CONFIG = {
    // Backend API URL
    // In production: points to your Render backend
    // In development: points to local backend
    API_BASE_URL: isProduction 
        ? 'https://clinical-copilot-api.onrender.com'  // UPDATE THIS after Render deployment
        : 'http://localhost:8000',
    
    // API endpoints
    endpoints: {
        health: '/health',
        analyze: '/analyze'
    }
};

// Helper function to get full API URL
function getApiUrl(endpoint) {
    return `${API_CONFIG.API_BASE_URL}${API_CONFIG.endpoints[endpoint] || endpoint}`;
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_CONFIG, getApiUrl };
}