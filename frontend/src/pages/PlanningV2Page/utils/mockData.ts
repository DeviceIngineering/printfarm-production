/**
 * Mock данные для разработки страницы планирования
 */

import { Printer, PrintTask } from '../types/printer.types';
import { Article } from '../types/article.types';
import { Queue, QueueTask } from '../types/queue.types';

/**
 * Генерация 27 принтеров P1S (3 ряда по 9 принтеров)
 */
export const mockPrinters: Printer[] = Array.from({ length: 27 }, (_, i) => {
  const printerNum = i + 1;
  const id = `P1S-${printerNum}`;

  // Случайный статус (80% печатают, 15% простаивают, 5% ошибка)
  const rand = Math.random();
  let status: 'printing' | 'idle' | 'error';
  if (rand < 0.8) status = 'printing';
  else if (rand < 0.95) status = 'idle';
  else status = 'error';

  // Распределение цветов: 50% black, 30% white, 20% other
  const colorRand = Math.random();
  let materialColor: 'black' | 'white' | 'other';
  if (colorRand < 0.5) materialColor = 'black';
  else if (colorRand < 0.8) materialColor = 'white';
  else materialColor = 'other';

  // Текущая задача (если печатает)
  const currentTask: PrintTask | null = status === 'printing' ? {
    article: `N421-${Math.floor(Math.random() * 90000 + 10000)}`,
    quantity: Math.floor(Math.random() * 20 + 5),
    progress: Math.floor(Math.random() * 100),
    timeRemaining: `${Math.floor(Math.random() * 3)}ч ${Math.floor(Math.random() * 60)}м`,
    startTime: new Date(Date.now() - Math.random() * 4 * 60 * 60 * 1000),
    endTime: new Date(Date.now() + Math.random() * 6 * 60 * 60 * 1000),
  } : null;

  // Очередь задач (1-3 задачи)
  const queueLength = Math.floor(Math.random() * 3);
  const queuedTasks: PrintTask[] = Array.from({ length: queueLength }, (_, j) => ({
    article: `N421-${Math.floor(Math.random() * 90000 + 10000)}`,
    quantity: Math.floor(Math.random() * 15 + 3),
    progress: 0,
    timeRemaining: `${Math.floor(Math.random() * 5)}ч ${Math.floor(Math.random() * 60)}м`,
    startTime: new Date(Date.now() + (j + 1) * 6 * 60 * 60 * 1000),
    endTime: new Date(Date.now() + (j + 2) * 6 * 60 * 60 * 1000),
  }));

  return {
    id,
    name: `Принтер ${printerNum}`,
    status,
    materialColor,
    currentTask,
    queuedTasks,
    temperature: {
      hotend: status === 'printing' ? Math.floor(Math.random() * 20 + 210) : 0,
      bed: status === 'printing' ? Math.floor(Math.random() * 10 + 60) : 0,
    },
  };
});

/**
 * Список артикулов на производство (~30 позиций)
 */
export const mockArticles: Article[] = [
  {
    id: 'N421-11-45K',
    name: 'Адаптер номерной рамки',
    priority: 'critical',
    currentStock: 2,
    sales2Months: 45,
    productionCapacity: '30шт/6ч',
    materialColor: 'black',
    currentlyPrinting: 15,
    queued48h: 30,
    printTimeSingle: 12,
  },
  {
    id: '375-42108',
    name: 'Заглушка круглая D42',
    priority: 'critical',
    currentStock: 3,
    sales2Months: 38,
    productionCapacity: '50шт/6ч',
    materialColor: 'black',
    currentlyPrinting: 0,
    queued48h: 0,
    printTimeSingle: 7,
  },
  {
    id: '381-40801',
    name: 'Крепеж для кабеля',
    priority: 'medium',
    currentStock: 12,
    sales2Months: 28,
    productionCapacity: '60шт/6ч',
    materialColor: 'white',
    currentlyPrinting: 20,
    queued48h: 40,
    printTimeSingle: 6,
  },
  {
    id: 'N421-22-50W',
    name: 'Корпус датчика (белый)',
    priority: 'medium',
    currentStock: 8,
    sales2Months: 22,
    productionCapacity: '25шт/6ч',
    materialColor: 'white',
    currentlyPrinting: 10,
    queued48h: 15,
    printTimeSingle: 14,
  },
  {
    id: '423-51412',
    name: 'Держатель провода',
    priority: 'low',
    currentStock: 18,
    sales2Months: 15,
    productionCapacity: '80шт/6ч',
    materialColor: 'black',
    currentlyPrinting: 0,
    queued48h: 0,
    printTimeSingle: 4,
  },
  // Добавляем еще 25 артикулов
  ...Array.from({ length: 25 }, (_, i) => {
    const num = i + 6;
    const priorities: ('critical' | 'medium' | 'low')[] = ['critical', 'medium', 'low'];
    const colors: ('black' | 'white' | 'other')[] = ['black', 'white', 'other'];

    return {
      id: `N${400 + num}-${Math.floor(Math.random() * 90000 + 10000)}`,
      name: `Деталь ${num}`,
      priority: priorities[Math.floor(Math.random() * 3)],
      currentStock: Math.floor(Math.random() * 25),
      sales2Months: Math.floor(Math.random() * 50),
      productionCapacity: `${Math.floor(Math.random() * 60 + 20)}шт/6ч`,
      materialColor: colors[Math.floor(Math.random() * 3)],
      currentlyPrinting: Math.floor(Math.random() * 30),
      queued48h: Math.floor(Math.random() * 50),
      printTimeSingle: Math.floor(Math.random() * 20 + 5),
    };
  }),
];

/**
 * Очереди печати (2 общие очереди)
 */
export const mockQueues: Queue[] = [
  {
    id: 'queue-1',
    name: 'Очередь критичных',
    tasks: [
      {
        id: 'task-1',
        article: 'N421-11-45K',
        articleName: 'Адаптер номерной рамки',
        quantity: 50,
        estimatedTime: '10ч 0м',
        priority: 'critical',
        materialColor: 'black',
      },
      {
        id: 'task-2',
        article: '375-42108',
        articleName: 'Заглушка круглая D42',
        quantity: 100,
        estimatedTime: '11ч 40м',
        priority: 'critical',
        materialColor: 'black',
      },
    ],
    totalTime: '21ч 40м',
  },
  {
    id: 'queue-2',
    name: 'Очередь стандартных',
    tasks: [
      {
        id: 'task-3',
        article: '381-40801',
        articleName: 'Крепеж для кабеля',
        quantity: 60,
        estimatedTime: '6ч 0м',
        priority: 'medium',
        materialColor: 'white',
      },
      {
        id: 'task-4',
        article: 'N421-22-50W',
        articleName: 'Корпус датчика (белый)',
        quantity: 30,
        estimatedTime: '7ч 0м',
        priority: 'medium',
        materialColor: 'white',
      },
    ],
    totalTime: '13ч 0м',
  },
];
