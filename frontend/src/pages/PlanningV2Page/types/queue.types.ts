/**
 * Типы для очередей печати
 */

export interface QueueTask {
  id: string;
  article: string;
  articleName: string;
  quantity: number;
  estimatedTime: string; // "2ч 30м"
  priority: 'critical' | 'medium' | 'low';
  materialColor: 'black' | 'white' | 'other';
}

export interface Queue {
  id: string;
  name: string;
  tasks: QueueTask[];
  totalTime: string; // "8ч 45м"
}
