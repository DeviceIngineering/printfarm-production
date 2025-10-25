import React, { useState, useEffect } from 'react';
import { Header } from './components/Header/Header';
import { LeftPanel } from './components/LeftPanel/LeftPanel';
import { Timeline } from './components/Timeline/Timeline';
import { BottomPanel } from './components/BottomPanel/BottomPanel';
import { mockPrinters, mockArticles, mockQueues } from './utils/mockData';
import { Printer } from './types/printer.types';
import { Article } from './types/article.types';
import { Queue } from './types/queue.types';
import './styles/PlanningV2Page.css';

export const PlanningV2Page: React.FC = () => {
  const [printers, setPrinters] = useState<Printer[]>(mockPrinters);
  const [articles, setArticles] = useState<Article[]>(mockArticles);
  const [queues, setQueues] = useState<Queue[]>(mockQueues);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());

  // Обновление текущего времени каждую секунду
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Обновление данных принтеров каждые 5 секунд
  useEffect(() => {
    const timer = setInterval(() => {
      // TODO: В будущем здесь будет вызов API для обновления данных
      // setPrinters(await fetchPrinters());
      console.log('Updating printer data...');
    }, 5000);

    return () => clearInterval(timer);
  }, []);

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
