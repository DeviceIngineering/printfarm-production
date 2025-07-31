import React from 'react';

function TestApp() {
  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#f0f0f0', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ color: '#06EAFC' }}>✅ React работает!</h1>
      <p>Если вы видите это сообщение, React приложение запущено корректно.</p>
      
      <h2>Проверка окружения:</h2>
      <ul>
        <li>API URL: {process.env.REACT_APP_API_URL || 'НЕ УСТАНОВЛЕН'}</li>
        <li>Media URL: {process.env.REACT_APP_MEDIA_URL || 'НЕ УСТАНОВЛЕН'}</li>
        <li>Node ENV: {process.env.NODE_ENV}</li>
      </ul>
      
      <h2>Отладочная информация:</h2>
      <pre style={{ backgroundColor: 'white', padding: '10px' }}>
        {JSON.stringify({
          timestamp: new Date().toISOString(),
          location: window.location.href,
          userAgent: navigator.userAgent
        }, null, 2)}
      </pre>
    </div>
  );
}

export default TestApp;