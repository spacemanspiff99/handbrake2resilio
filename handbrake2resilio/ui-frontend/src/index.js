import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

console.log('🔧 React index.js starting...');
console.log('🔧 Environment variables:', {
  NODE_ENV: process.env.NODE_ENV,
  REACT_APP_API_URL: process.env.REACT_APP_API_URL,
  REACT_APP_WS_URL: process.env.REACT_APP_WS_URL
});

try {
  const rootElement = document.getElementById('root');
  console.log(' Root element found:', rootElement);
  
  if (!rootElement) {
    throw new Error('Root element not found!');
  }

  const root = ReactDOM.createRoot(rootElement);
  console.log(' React root created successfully');
  
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
  
  console.log(' React app rendered successfully');
} catch (error) {
  console.error('🚨 CRITICAL ERROR in React mounting:', error);
  console.error('🚨 Error stack:', error.stack);
  
  // Log to server
  try {
    fetch('/api/log-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.toString(),
        stack: error.stack,
        type: 'react_mounting_error',
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: new Date().toISOString()
      })
    });
  } catch (e) {
    console.error('Failed to log mounting error to server:', e);
  }
  
  // Display error on page
  const rootElement = document.getElementById('root');
  if (rootElement) {
    rootElement.innerHTML = `
      <div style="padding: 20px; background: #fee; border: 1px solid #fcc; margin: 20px;">
        <h1>🚨 Critical React Error</h1>
        <p><strong>Error:</strong> ${error.message}</p>
        <details style="white-space: pre-wrap; margin-top: 10px;">
          <summary>Error Details</summary>
          <pre>${error.stack}</pre>
        </details>
        <p><em>This error has been logged to the server.</em></p>
      </div>
    `;
  }
}