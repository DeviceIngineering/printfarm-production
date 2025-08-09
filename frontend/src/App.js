import React from 'react';
import { ConfigProvider } from 'antd';
import ruRU from 'antd/locale/ru_RU';
import './App.css';

function App() {
  return (
    <ConfigProvider locale={ruRU}>
      <div className="App">
        <header className="App-header">
          <h1>🏭 PrintFarm Production System</h1>
          <p>Система управления производством готова к работе!</p>
          <div className="status-indicators">
            <div className="status-item">
              <span className="status-dot success"></span>
              Frontend: Готов
            </div>
            <div className="status-item">
              <span className="status-dot success"></span>
              Backend: Подключается...
            </div>
            <div className="status-item">
              <span className="status-dot success"></span>
              Автодеплой: Активен
            </div>
          </div>
        </header>
      </div>
    </ConfigProvider>
  );
}

export default App;