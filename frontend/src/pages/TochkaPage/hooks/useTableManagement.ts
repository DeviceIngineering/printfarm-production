/**
 * Hook для управления таблицами и их состоянием
 * Включает пагинацию, сворачивание и SimplePrint обогащение
 */
import { useState } from 'react';
import { message } from 'antd';
import { apiClient } from '../../../api/client';
import type { TablesCollapsedState } from './useExcelUpload';

interface UseTableManagementReturn {
  // Pagination states
  productsPageSize: number;
  setProductsPageSize: (size: number) => void;
  productionPageSize: number;
  setProductionPageSize: (size: number) => void;
  mergedDataPageSize: number;
  setMergedDataPageSize: (size: number) => void;
  excelDataPageSize: number;
  setExcelDataPageSize: (size: number) => void;
  deduplicatedPageSize: number;
  setDeduplicatedPageSize: (size: number) => void;
  filteredProductionPageSize: number;
  setFilteredProductionPageSize: (size: number) => void;

  // SimplePrint state
  showSimpleprintColumns: boolean;
  enrichedProductionData: any[];
  handleEnrichFromSimplePrint: (filteredProductionData: any[]) => Promise<void>;

  // Table collapse
  toggleTableCollapse: (tableKey: keyof TablesCollapsedState, tablesCollapsed: TablesCollapsedState, setTablesCollapsed: React.Dispatch<React.SetStateAction<TablesCollapsedState>>) => void;
  createCollapsibleTitle: (title: string, tableKey: keyof TablesCollapsedState, tablesCollapsed: TablesCollapsedState, setTablesCollapsed: React.Dispatch<React.SetStateAction<TablesCollapsedState>>, extra?: React.ReactNode) => JSX.Element;
}

export const useTableManagement = (): UseTableManagementReturn => {
  // Pagination state для каждой таблицы
  const [productsPageSize, setProductsPageSize] = useState(20);
  const [productionPageSize, setProductionPageSize] = useState(20);
  const [mergedDataPageSize, setMergedDataPageSize] = useState(20);
  const [excelDataPageSize, setExcelDataPageSize] = useState(20);
  const [deduplicatedPageSize, setDeduplicatedPageSize] = useState(20);
  const [filteredProductionPageSize, setFilteredProductionPageSize] = useState(20);

  // State для отображения SimplePrint колонок
  const [showSimpleprintColumns, setShowSimpleprintColumns] = useState(false);
  const [enrichedProductionData, setEnrichedProductionData] = useState<any[]>([]);

  /**
   * Функция для обогащения данных из SimplePrint
   */
  const handleEnrichFromSimplePrint = async (filteredProductionData: any[]) => {
    try {
      message.loading({ content: 'Загрузка данных SimplePrint...', key: 'enrichSP', duration: 0 });

      // Получаем ВСЕ файлы из SimplePrint (page_size=2000 для 1587 файлов)
      const response: any = await apiClient.get('/simpleprint/files/?page_size=2000');
      const spFiles = response.results || response;

      if (!spFiles || spFiles.length === 0) {
        message.warning({ content: 'Нет данных SimplePrint для обогащения', key: 'enrichSP' });
        return;
      }

      // Группируем файлы по артикулу (РЕГИСТРОНЕЗАВИСИМО) и находим максимальные значения
      const articleMaxValues: { [key: string]: { maxPrintTime: number; maxQuantity: number } } = {};

      spFiles.forEach((file: any) => {
        const article = file.article;
        if (!article) return; // Пропускаем файлы без артикула

        // Приводим к нижнему регистру для регистронезависимого сопоставления
        const articleLower = article.toLowerCase();

        const printTime = file.print_time || 0;
        const quantity = file.quantity || 0;

        if (!articleMaxValues[articleLower]) {
          articleMaxValues[articleLower] = {
            maxPrintTime: printTime,
            maxQuantity: quantity
          };
        } else {
          // Обновляем максимальные значения
          if (printTime > articleMaxValues[articleLower].maxPrintTime) {
            articleMaxValues[articleLower].maxPrintTime = printTime;
          }
          if (quantity > articleMaxValues[articleLower].maxQuantity) {
            articleMaxValues[articleLower].maxQuantity = quantity;
          }
        }
      });

      // Обогащаем filteredProductionData данными из SimplePrint
      const enriched = filteredProductionData.map((item: any) => {
        const article = item.article;
        // Приводим к нижнему регистру для регистронезависимого сопоставления
        const articleLower = article ? article.toLowerCase() : '';
        const spData = articleMaxValues[articleLower];

        return {
          ...item,
          sp_max_print_time: spData?.maxPrintTime || null,
          sp_max_quantity: spData?.maxQuantity || null,
          has_sp_data: !!spData
        };
      });

      setEnrichedProductionData(enriched);
      setShowSimpleprintColumns(true);

      const foundCount = enriched.filter((item: any) => item.has_sp_data).length;
      message.success({
        content: `Данные обогащены! Найдено SimplePrint данных: ${foundCount}/${enriched.length}`,
        key: 'enrichSP',
        duration: 5
      });

    } catch (error: any) {
      console.error('Ошибка при обогащении данных:', error);
      message.error({ content: error.message || 'Ошибка при загрузке данных SimplePrint', key: 'enrichSP' });
    }
  };

  /**
   * Функция для переключения сворачивания таблиц
   */
  const toggleTableCollapse = (
    tableKey: keyof TablesCollapsedState,
    tablesCollapsed: TablesCollapsedState,
    setTablesCollapsed: React.Dispatch<React.SetStateAction<TablesCollapsedState>>
  ) => {
    setTablesCollapsed(prev => ({
      ...prev,
      [tableKey]: !prev[tableKey]
    }));
  };

  /**
   * Вспомогательная функция для создания заголовка карточки с кнопкой сворачивания
   */
  const createCollapsibleTitle = (
    title: string,
    tableKey: keyof TablesCollapsedState,
    tablesCollapsed: TablesCollapsedState,
    setTablesCollapsed: React.Dispatch<React.SetStateAction<TablesCollapsedState>>,
    extra?: React.ReactNode
  ): JSX.Element => {
    const isCollapsed = tablesCollapsed[tableKey];
    const { Button } = require('antd');
    const { UpOutlined, DownOutlined } = require('@ant-design/icons');

    return (
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
        <span>{title}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {extra}
          <Button
            type="text"
            size="small"
            icon={isCollapsed ? <DownOutlined /> : <UpOutlined />}
            onClick={() => toggleTableCollapse(tableKey, tablesCollapsed, setTablesCollapsed)}
            style={{
              padding: '0 4px',
              color: '#1890ff',
              border: 'none'
            }}
            title={isCollapsed ? 'Развернуть таблицу' : 'Свернуть таблицу'}
          />
        </div>
      </div>
    );
  };

  return {
    // Pagination states
    productsPageSize,
    setProductsPageSize,
    productionPageSize,
    setProductionPageSize,
    mergedDataPageSize,
    setMergedDataPageSize,
    excelDataPageSize,
    setExcelDataPageSize,
    deduplicatedPageSize,
    setDeduplicatedPageSize,
    filteredProductionPageSize,
    setFilteredProductionPageSize,

    // SimplePrint
    showSimpleprintColumns,
    enrichedProductionData,
    handleEnrichFromSimplePrint,

    // Table collapse
    toggleTableCollapse,
    createCollapsibleTitle,
  };
};
