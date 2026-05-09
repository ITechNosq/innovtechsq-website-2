// Innovtechnosq - Global Configuration
window.CONFIG = {
    // WhatsApp Integration
    WHATSAPP_NUMBER: '918595237962',
    WHATSAPP_MESSAGE: 'Hi Innovtechnosq, I would like to submit a Service Request (SR) for my business.',
    
    // API Configuration
    API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8000' 
        : 'https://api.innovtechnosq.co.in',
        
    // UI Settings
    THEME: 'dark-glass',
    SR_PREFIX: 'SR-',
};
