import React, { useState } from 'react';
import { Card, Statistic, Row, Col, Tag, Collapse, Timeline, Typography, Space, Badge } from 'antd';
import { InfoCircleOutlined, HistoryOutlined, CheckCircleOutlined, BugOutlined, GithubOutlined } from '@ant-design/icons';
import { SystemInfo as SystemInfoType } from '../../api/settings';
import { CHANGELOG } from '../../data/changelog';

const { Panel } = Collapse;
const { Text, Paragraph } = Typography;

interface SystemInfoProps {
  systemInfo: SystemInfoType | null;
  loading?: boolean;
}

export const SystemInfo: React.FC<SystemInfoProps> = ({ systemInfo, loading = false }) => {
  const [activeKey, setActiveKey] = useState<string | string[]>([]);

  return (
    <Card
      title={
        <span>
          <InfoCircleOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
          Информация о системе
        </span>
      }
      loading={loading}
    >
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Statistic
            title="Версия системы"
            value={systemInfo?.version || 'Неизвестно'}
            prefix={<Tag color="cyan">v</Tag>}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="Дата сборки"
            value={systemInfo?.build_date || 'Неизвестно'}
          />
        </Col>
      </Row>

      {/* Разворачивающийся лог изменений */}
      <Collapse
        activeKey={activeKey}
        onChange={setActiveKey}
        style={{ marginTop: 16 }}
      >
        <Panel
          header={
            <Space>
              <HistoryOutlined style={{ color: 'var(--color-primary)' }} />
              <Text strong>История изменений проекта</Text>
              <Badge count={CHANGELOG.length} style={{ backgroundColor: '#52c41a' }} />
            </Space>
          }
          key="changelog"
        >
          <Timeline mode="left" style={{ marginTop: 16 }}>
            {CHANGELOG.map((entry, index) => (
              <Timeline.Item
                key={entry.version}
                color={index === 0 ? 'green' : 'blue'}
                dot={index === 0 ? <CheckCircleOutlined style={{ fontSize: '16px' }} /> : undefined}
              >
                <div style={{ paddingBottom: 24 }}>
                  {/* Заголовок версии */}
                  <Space align="center" style={{ marginBottom: 8 }}>
                    <Tag color={index === 0 ? 'success' : 'processing'} style={{ fontSize: '14px', padding: '2px 8px' }}>
                      v{entry.version}
                    </Tag>
                    <Text type="secondary" style={{ fontSize: '13px' }}>{entry.date}</Text>
                    {index === 0 && <Tag color="gold">ТЕКУЩАЯ</Tag>}
                  </Space>

                  {/* Название релиза */}
                  <Paragraph strong style={{ marginBottom: 12, fontSize: '15px' }}>
                    {entry.title}
                  </Paragraph>

                  {/* Новые возможности */}
                  {entry.features && entry.features.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <Space align="start" style={{ marginBottom: 4 }}>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginTop: 4 }} />
                        <Text strong style={{ color: '#52c41a' }}>Новые возможности:</Text>
                      </Space>
                      <ul style={{ marginLeft: 24, marginTop: 4, marginBottom: 0 }}>
                        {entry.features.map((feature, idx) => (
                          <li key={idx}>
                            <Text style={{ fontSize: '13px' }}>{feature}</Text>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Исправления */}
                  {entry.fixes && entry.fixes.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <Space align="start" style={{ marginBottom: 4 }}>
                        <BugOutlined style={{ color: '#faad14', marginTop: 4 }} />
                        <Text strong style={{ color: '#faad14' }}>Исправления:</Text>
                      </Space>
                      <ul style={{ marginLeft: 24, marginTop: 4, marginBottom: 0 }}>
                        {entry.fixes.map((fix, idx) => (
                          <li key={idx}>
                            <Text style={{ fontSize: '13px' }}>{fix}</Text>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Коммиты */}
                  {entry.commits && entry.commits.length > 0 && (
                    <div>
                      <Space align="start" style={{ marginBottom: 4 }}>
                        <GithubOutlined style={{ color: '#8c8c8c', marginTop: 4 }} />
                        <Text type="secondary" style={{ fontSize: '12px' }}>Коммиты:</Text>
                      </Space>
                      <ul style={{ marginLeft: 24, marginTop: 4, marginBottom: 0 }}>
                        {entry.commits.slice(0, 3).map((commit, idx) => (
                          <li key={idx}>
                            <Text type="secondary" style={{ fontSize: '12px', fontFamily: 'monospace' }}>
                              {commit}
                            </Text>
                          </li>
                        ))}
                        {entry.commits.length > 3 && (
                          <li>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              ... и еще {entry.commits.length - 3} коммитов
                            </Text>
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              </Timeline.Item>
            ))}
          </Timeline>

          {/* Статистика в конце */}
          <div style={{
            marginTop: 24,
            padding: 16,
            background: '#f0f2f5',
            borderRadius: 8,
            textAlign: 'center'
          }}>
            <Space size="large">
              <Statistic
                title="Всего релизов"
                value={CHANGELOG.length}
                valueStyle={{ fontSize: '20px', color: '#1890ff' }}
              />
              <Statistic
                title="Текущая версия"
                value={CHANGELOG[0]?.version || 'N/A'}
                prefix="v"
                valueStyle={{ fontSize: '20px', color: '#52c41a' }}
              />
            </Space>
          </div>
        </Panel>
      </Collapse>
    </Card>
  );
};