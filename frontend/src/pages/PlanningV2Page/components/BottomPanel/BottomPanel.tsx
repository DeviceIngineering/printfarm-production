import React from 'react';
import { Tag, Tooltip, Button } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { Queue } from '../../types/queue.types';
import './BottomPanel.css';

interface BottomPanelProps {
  queues: Queue[];
}

export const BottomPanel: React.FC<BottomPanelProps> = ({ queues }) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const handleRemoveTask = (queueId: string, taskId: string) => {
    console.log('Remove task:', taskId, 'from queue:', queueId);
    // TODO: Удалить задачу из очереди
  };

  const handleAddQueue = () => {
    console.log('Add new queue');
    // TODO: Добавить новую очередь
  };

  return (
    <div className="planning-v2-bottom-panel">
      <div className="bottom-panel-header">
        <h3>Очереди печати</h3>
        <Button
          type="dashed"
          size="small"
          icon={<PlusOutlined />}
          onClick={handleAddQueue}
        >
          Добавить очередь
        </Button>
      </div>

      <div className="bottom-panel-queues">
        {queues.map(queue => (
          <div key={queue.id} className="queue-container">
            <div className="queue-header">
              <div className="queue-info">
                <span className="queue-name">{queue.name}</span>
                <Tag color="blue">{queue.tasks.length} задач</Tag>
                <Tag color="cyan">{queue.totalTime}</Tag>
              </div>
            </div>

            <div
              className="queue-tasks"
              onDrop={(e) => {
                e.preventDefault();
                const articleData = e.dataTransfer.getData('article');
                console.log('Dropped on queue:', queue.id, articleData);
                // TODO: Добавить задачу в очередь
              }}
              onDragOver={(e) => e.preventDefault()}
            >
              {queue.tasks.map(task => (
                <div key={task.id} className="queue-task-card">
                  <div className="queue-task-header">
                    <span className="queue-task-article">{task.article}</span>
                    <Tag color={getPriorityColor(task.priority)} style={{ fontSize: '10px' }}>
                      {task.priority === 'critical' ? 'Крит.' : task.priority === 'medium' ? 'Сред.' : 'Низк.'}
                    </Tag>
                  </div>

                  <div className="queue-task-name">{task.articleName}</div>

                  <div className="queue-task-stats">
                    <div className="queue-task-stat">
                      <span className="queue-stat-label">Количество:</span>
                      <span className="queue-stat-value">{task.quantity} шт</span>
                    </div>
                    <div className="queue-task-stat">
                      <span className="queue-stat-label">Время:</span>
                      <span className="queue-stat-value">{task.estimatedTime}</span>
                    </div>
                  </div>

                  <div className="queue-task-footer">
                    <Tag
                      color={task.materialColor === 'black' ? 'default' : task.materialColor === 'white' ? 'blue' : 'purple'}
                      style={{ fontSize: '10px' }}
                    >
                      {task.materialColor === 'black' ? 'Черный' : task.materialColor === 'white' ? 'Белый' : 'Другой'}
                    </Tag>
                    <Tooltip title="Удалить из очереди">
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleRemoveTask(queue.id, task.id)}
                      />
                    </Tooltip>
                  </div>
                </div>
              ))}

              {queue.tasks.length === 0 && (
                <div className="queue-empty">
                  <p>Перетащите артикулы сюда</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
