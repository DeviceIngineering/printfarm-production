import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Header } from './components/Header/Header';
import { LeftPanel } from './components/LeftPanel/LeftPanel';
import { Timeline } from './components/Timeline/Timeline';
import { BottomPanel } from './components/BottomPanel/BottomPanel';
import { mockArticles, mockQueues } from './utils/mockData';
import { Printer } from './types/printer.types';
import { Article } from './types/article.types';
import { Queue } from './types/queue.types';
import { fetchPrinters } from '../../store/simpleprintPrintersSlice';
import { RootState, AppDispatch } from '../../store';
import { mapSimplePrintsToPrinters } from './utils/printerMapper';
import './styles/PlanningV2Page.css';

export const PlanningV2Page: React.FC = () => {
  console.log('🚀 PlanningV2Page component rendered');

  const dispatch = useDispatch<AppDispatch>();

  console.log('🔍 Selecting state...');
  const reduxState = useSelector((state: RootState) => state);
  console.log('🔍 Full Redux state:', reduxState);
  console.log('🔍 simpleprintPrinters key exists?', 'simpleprintPrinters' in reduxState);

  const { printers: simpleprintPrinters, loading, error } = useSelector((state: RootState) => state.simpleprintPrinters);

  // Преобразуем SimplePrint данные в формат Printer и сортируем по имени
  const printers = mapSimplePrintsToPrinters(simpleprintPrinters).sort((a, b) => {
    // Извлекаем номер из имени принтера (например "P1S-10" -> 10)
    const numA = parseInt(a.name.split('-')[1] || '0');
    const numB = parseInt(b.name.split('-')[1] || '0');
    return numA - numB;
  });

  // Отладка
  useEffect(() => {
    console.log('🔍 SimplePrint printers from Redux:', simpleprintPrinters);
    console.log('🔍 Mapped printers:', printers);
    console.log('🔍 Loading:', loading);
    console.log('🔍 Error:', error);
  }, [simpleprintPrinters, printers, loading, error]);

  const [articles, setArticles] = useState<Article[]>(mockArticles);
  const [queues, setQueues] = useState<Queue[]>(mockQueues);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());

  // Загрузка данных при монтировании компонента
  useEffect(() => {
    // Начальная загрузка
    console.log('📡 Fetching printers...');
    dispatch(fetchPrinters());
  }, [dispatch]);

  // Обновление текущего времени каждую секунду
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Обновление данных принтеров каждые 30 секунд
  useEffect(() => {
    const timer = setInterval(() => {
      dispatch(fetchPrinters());
    }, 30000); // 30 секунд

    return () => clearInterval(timer);
  }, [dispatch]);

  // Индикатор загрузки
  if (loading && printers.length === 0) {
    return (
      <div className="planning-v2-page">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontSize: '24px', color: '#06EAFC' }}>
          Загрузка принтеров...
        </div>
      </div>
    );
  }

  // Индикатор ошибки
  if (error && printers.length === 0) {
    return (
      <div className="planning-v2-page">
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100vh', color: '#ff4d4f' }}>
          <div style={{ fontSize: '24px', marginBottom: '16px' }}>❌ Ошибка загрузки принтеров</div>
          <div style={{ fontSize: '16px' }}>{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="planning-v2-page">
      <Header currentTime={currentTime} printers={printers} />

      <div className="planning-v2-content">
        <div className="planning-v2-main-layout">
          {/* Левая панель с артикулами */}
          <LeftPanel articles={articles} />

          {/* Центральная часть с таймлайном принтеров */}
          <Timeline
            printers={printers}
            currentTime={currentTime}
          />
        </div>

        {/* Нижняя панель с очередями */}
        <BottomPanel queues={queues} />
      </div>
    </div>
  );
};
