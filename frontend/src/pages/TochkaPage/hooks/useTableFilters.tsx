/**
 * Hook для фильтрации и поиска в таблицах
 * Содержит логику поиска по артикулу и фильтрации по значениям
 */
import { useState, useRef } from 'react';
import { Input, Button, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

interface UseTableFiltersReturn {
  searchText: string;
  searchedColumn: string;
  searchInput: React.MutableRefObject<any>;
  getColumnSearchProps: (dataIndex: string) => any;
  getColumnFilterProps: (dataIndex: string, data: any[]) => any;
  handleSearch: (selectedKeys: any, confirm: any, dataIndex: any) => void;
  handleReset: (clearFilters: any) => void;
}

export const useTableFilters = (): UseTableFiltersReturn => {
  const [searchText, setSearchText] = useState('');
  const [searchedColumn, setSearchedColumn] = useState('');
  const searchInput = useRef<any>(null);

  /**
   * Обработчик поиска
   */
  const handleSearch = (selectedKeys: any, confirm: any, dataIndex: any) => {
    confirm();
    setSearchText(selectedKeys[0]);
    setSearchedColumn(dataIndex);
  };

  /**
   * Обработчик сброса фильтра
   */
  const handleReset = (clearFilters: any) => {
    clearFilters();
    setSearchText('');
  };

  /**
   * Функция для создания props поиска по колонке
   */
  const getColumnSearchProps = (dataIndex: string) => ({
    filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
      <div style={{ padding: 8 }}>
        <Input
          ref={searchInput}
          placeholder={`Поиск артикула`}
          value={selectedKeys[0]}
          onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
          onPressEnter={() => handleSearch(selectedKeys, confirm, dataIndex)}
          style={{ marginBottom: 8, display: 'block' }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys, confirm, dataIndex)}
            icon={<SearchOutlined />}
            size="small"
            style={{ width: 90 }}
          >
            Найти
          </Button>
          <Button
            onClick={() => clearFilters && handleReset(clearFilters)}
            size="small"
            style={{ width: 90 }}
          >
            Сбросить
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    onFilter: (value: any, record: any) =>
      record[dataIndex]
        ? record[dataIndex].toString().toLowerCase().includes(value.toLowerCase())
        : '',
    onFilterDropdownVisibleChange: (visible: boolean) => {
      if (visible) {
        setTimeout(() => searchInput.current?.select(), 100);
      }
    },
  });

  /**
   * Функция для создания фильтра по значениям (например, для цвета)
   */
  const getColumnFilterProps = (dataIndex: string, data: any[]) => {
    // Получаем уникальные значения из данных
    const uniqueValues = Array.from(new Set(
      data.map(item => {
        const value = item[dataIndex];
        return value || 'Не указан';
      })
    )).sort();

    return {
      filters: uniqueValues.map(value => ({
        text: value,
        value: value === 'Не указан' ? '' : value,
      })),
      onFilter: (value: any, record: any) => {
        const recordValue = record[dataIndex] || '';
        return recordValue === value;
      },
    };
  };

  return {
    searchText,
    searchedColumn,
    searchInput,
    getColumnSearchProps,
    getColumnFilterProps,
    handleSearch,
    handleReset,
  };
};
