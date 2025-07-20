import React, { useEffect } from 'react';
import { Button, Card, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  const handleLogin = () => {
    // Set the demo token
    localStorage.setItem('auth_token', '549ebaf641ffa608a26b79a21d72a296c99a02b7');
    navigate('/');
  };

  useEffect(() => {
    // Auto-login for demo
    const token = localStorage.getItem('auth_token');
    if (token) {
      navigate('/');
    }
  }, [navigate]);

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center',
      background: 'linear-gradient(135deg, #1e1e1e 0%, #06EAFC 100%)'
    }}>
      <Card style={{ width: 400, textAlign: 'center' }}>
        <Title level={2} style={{ color: '#06EAFC', marginBottom: 24 }}>
          PrintFarm
        </Title>
        <Text style={{ display: 'block', marginBottom: 24 }}>
          Система управления производством
        </Text>
        <Button 
          type="primary" 
          size="large" 
          onClick={handleLogin}
          style={{ width: '100%' }}
          className="btn-primary"
        >
          Войти в систему
        </Button>
      </Card>
    </div>
  );
};