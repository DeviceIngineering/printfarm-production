import React, { useState } from 'react';
import { Input, Select, Badge, Tag } from 'antd';
import { SearchOutlined, FilterOutlined } from '@ant-design/icons';
import { Article } from '../../types/article.types';
import './LeftPanel.css';

const { Option } = Select;

interface LeftPanelProps {
  articles: Article[];
}

export const LeftPanel: React.FC<LeftPanelProps> = ({ articles }) => {
  const [searchText, setSearchText] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [colorFilter, setColorFilter] = useState<string>('all');

  // Фильтрация артикулов
  const filteredArticles = articles.filter(article => {
    const matchesSearch = article.id.toLowerCase().includes(searchText.toLowerCase()) ||
                         article.name.toLowerCase().includes(searchText.toLowerCase());
    const matchesPriority = priorityFilter === 'all' || article.priority === priorityFilter;
    const matchesColor = colorFilter === 'all' || article.materialColor === colorFilter;

    return matchesSearch && matchesPriority && matchesColor;
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'critical': return 'Крит.';
      case 'medium': return 'Сред.';
      case 'low': return 'Низк.';
      default: return priority;
    }
  };

  return (
    <div className="planning-v2-left-panel">
      <div className="left-panel-header">
        <h3>Артикулы на производство</h3>
        <Badge count={filteredArticles.length} showZero style={{ backgroundColor: '#52c41a' }} />
      </div>

      <div className="left-panel-filters">
        <Input
          placeholder="Поиск по артикулу..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          allowClear
        />

        <Select
          value={priorityFilter}
          onChange={setPriorityFilter}
          style={{ width: '100%' }}
          suffixIcon={<FilterOutlined />}
        >
          <Option value="all">Все приоритеты</Option>
          <Option value="critical">Критичные</Option>
          <Option value="medium">Средние</Option>
          <Option value="low">Низкие</Option>
        </Select>

        <Select
          value={colorFilter}
          onChange={setColorFilter}
          style={{ width: '100%' }}
          suffixIcon={<FilterOutlined />}
        >
          <Option value="all">Все цвета</Option>
          <Option value="black">Черный</Option>
          <Option value="white">Белый</Option>
          <Option value="other">Другой</Option>
        </Select>
      </div>

      <div className="left-panel-articles">
        {filteredArticles.map(article => (
          <div
            key={article.id}
            className="article-card"
            draggable
            onDragStart={(e) => {
              e.dataTransfer.setData('article', JSON.stringify(article));
            }}
          >
            <div className="article-card-header">
              <span className="article-id">{article.id}</span>
              <Tag color={getPriorityColor(article.priority)} className="article-priority">
                {getPriorityText(article.priority)}
              </Tag>
            </div>

            <div className="article-stats-compact">
              <div className="stat-item">
                <span className="stat-label">Ост:</span>
                <span className="stat-value">{article.currentStock}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Печ:</span>
                <span className="stat-value printing">{article.currentlyPrinting}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Оч:</span>
                <span className="stat-value queued">{article.queued48h}</span>
              </div>
            </div>
          </div>
        ))}

        {filteredArticles.length === 0 && (
          <div className="left-panel-empty">
            <p>Нет артикулов</p>
          </div>
        )}
      </div>
    </div>
  );
};
