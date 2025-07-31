import React, { useEffect, useState } from 'react';
import { Alert } from 'antd';

export const DebugInfo: React.FC = () => {
  const [debugData, setDebugData] = useState<any>({});

  useEffect(() => {
    const data = {
      token: localStorage.getItem('auth_token'),
      apiUrl: process.env.REACT_APP_API_URL || 'NOT SET',
      mediaUrl: process.env.REACT_APP_MEDIA_URL || 'NOT SET',
      nodeEnv: process.env.NODE_ENV,
      timestamp: new Date().toISOString(),
      windowLocation: window.location.href
    };
    setDebugData(data);
    console.log('Debug Info:', data);
  }, []);

  // Только в development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <Alert
      message="Debug Info (Development Only)"
      description={
        <pre style={{ fontSize: '12px', margin: 0 }}>
          {JSON.stringify(debugData, null, 2)}
        </pre>
      }
      type="info"
      closable
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        maxWidth: 400,
        zIndex: 9999
      }}
    />
  );
};