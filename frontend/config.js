// Configuration for the frontend
window.API_BASE_URL = 'http://localhost:5000'; // Default local development
// For Netlify, you can override this or manualy change it before deploy
// Or better, use a relative path if you proxy /api calls.
// However, since we are doing cors, we might need the full URL if hosted elsewhere.
// But for this task, the requirements said "Generate /frontend/config.js template"

console.log('API Base URL:', window.API_BASE_URL);
