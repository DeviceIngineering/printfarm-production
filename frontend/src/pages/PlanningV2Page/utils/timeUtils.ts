/**
 * Утилиты для работы со временем (GMT+3)
 */

/**
 * Получить текущее время в GMT+3
 */
export const getCurrentTimeGMT3 = (): Date => {
  const now = new Date();
  // Получаем UTC время и добавляем 3 часа
  const utc = now.getTime() + now.getTimezoneOffset() * 60000;
  return new Date(utc + 3 * 60 * 60 * 1000);
};

/**
 * Форматировать время для отображения на таймлайне
 */
export const formatTimeForTimeline = (date: Date): string => {
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
};

/**
 * Форматировать дату для заголовка (например: "25 окт, Пт")
 */
export const formatDateHeader = (date: Date): string => {
  const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
  const weekDays = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

  const day = date.getDate();
  const month = months[date.getMonth()];
  const weekDay = weekDays[date.getDay()];

  return `${day} ${month}, ${weekDay}`;
};

/**
 * Получить массив временных отметок для таймлайна (-4ч до +48ч)
 */
export const getTimelineHours = (): Date[] => {
  const now = getCurrentTimeGMT3();
  const startTime = new Date(now.getTime() - 4 * 60 * 60 * 1000); // -4 часа

  const hours: Date[] = [];
  for (let i = 0; i < 53; i++) { // -4ч до +48ч = 52 часа + текущий
    hours.push(new Date(startTime.getTime() + i * 60 * 60 * 1000));
  }

  return hours;
};

/**
 * Рассчитать позицию элемента на таймлайне (в процентах)
 */
export const calculateTimelinePosition = (time: Date): number => {
  const now = getCurrentTimeGMT3();
  const startTime = new Date(now.getTime() - 4 * 60 * 60 * 1000);
  const totalDuration = 52 * 60 * 60 * 1000; // 52 часа в мс

  const offset = time.getTime() - startTime.getTime();
  return (offset / totalDuration) * 100;
};

/**
 * Рассчитать ширину элемента на таймлайне (в процентах)
 */
export const calculateTimelineWidth = (startTime: Date, endTime: Date): number => {
  const duration = endTime.getTime() - startTime.getTime();
  const totalDuration = 52 * 60 * 60 * 1000; // 52 часа в мс

  return (duration / totalDuration) * 100;
};

/**
 * Проверить, находится ли время в диапазоне таймлайна
 */
export const isTimeInTimeline = (time: Date): boolean => {
  const now = getCurrentTimeGMT3();
  const startTime = new Date(now.getTime() - 4 * 60 * 60 * 1000);
  const endTime = new Date(now.getTime() + 48 * 60 * 60 * 1000);

  return time >= startTime && time <= endTime;
};

/**
 * Парсить строку времени "2ч 30м" в минуты
 */
export const parseTimeString = (timeStr: string): number => {
  const hoursMatch = timeStr.match(/(\d+)ч/);
  const minutesMatch = timeStr.match(/(\d+)м/);

  const hours = hoursMatch ? parseInt(hoursMatch[1], 10) : 0;
  const minutes = minutesMatch ? parseInt(minutesMatch[1], 10) : 0;

  return hours * 60 + minutes;
};

/**
 * Форматировать минуты в строку "2ч 30м"
 */
export const formatMinutesToTimeString = (minutes: number): string => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  if (hours === 0) return `${mins}м`;
  if (mins === 0) return `${hours}ч`;
  return `${hours}ч ${mins}м`;
};
