/**
 * Типы для артикулов
 */

export type Priority = 'critical' | 'medium' | 'low';
export type MaterialColor = 'black' | 'white' | 'other';

export interface Article {
  id: string; // "N421-11-45K"
  name: string; // "Адаптер номерной рамки"
  priority: Priority;
  currentStock: number; // штук на складе
  sales2Months: number; // продано за 2 месяца
  productionCapacity: string; // "30шт/6ч"
  materialColor: MaterialColor;
  currentlyPrinting: number; // штук печатается сейчас
  queued48h: number; // штук запланировано на 48 часов
  printTimeSingle?: number; // время печати одной штуки в минутах
}
