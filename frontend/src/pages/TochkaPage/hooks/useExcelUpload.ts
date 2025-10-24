/**
 * Hook для управления загрузкой и обработкой Excel файлов
 * Инкапсулирует логику загрузки файлов и обработки результатов
 */
import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { message } from 'antd';
import { AppDispatch } from '../../../store';
import {
  uploadAndAutoProcess,
  exportDeduplicated,
  exportProduction,
} from '../../../store/tochka';

interface UseExcelUploadReturn {
  uploadModalVisible: boolean;
  setUploadModalVisible: (visible: boolean) => void;
  handleExcelUpload: (file: File) => Promise<boolean>;
  handleExportDeduplicatedExcel: (data: any[]) => Promise<void>;
  handleExportProductionList: (data: any[]) => Promise<void>;
  setTablesCollapsed: React.Dispatch<React.SetStateAction<TablesCollapsedState>>;
  tablesCollapsed: TablesCollapsedState;
}

export interface TablesCollapsedState {
  products: boolean;
  production: boolean;
  mergedData: boolean;
  excelData: boolean;
  deduplicatedData: boolean;
  filteredProduction: boolean;
}

export const useExcelUpload = (): UseExcelUploadReturn => {
  const dispatch = useDispatch<AppDispatch>();
  const [uploadModalVisible, setUploadModalVisible] = useState(false);

  // Состояния для сворачивания таблиц
  const [tablesCollapsed, setTablesCollapsed] = useState<TablesCollapsedState>({
    products: false,
    production: false,
    mergedData: true, // свернуто по умолчанию после обработки
    excelData: true, // свернуто по умолчанию после обработки
    deduplicatedData: true, // свернуто по умолчанию после обработки
    filteredProduction: false // основная таблица результата - развернута
  });

  /**
   * Обработка загрузки Excel файла с автоматической обработкой
   */
  const handleExcelUpload = async (file: File): Promise<boolean> => {
    try {
      const result = await dispatch(uploadAndAutoProcess(file)).unwrap();
      setUploadModalVisible(false);

      // Показываем результат автоматической обработки
      const { summary } = result;
      const successMessage = `Файл обработан за ${result.processing_time_seconds.toFixed(1)}с! ` +
        `Найдено товаров: ${summary.products_found_in_db}/${summary.total_excel_records} ` +
        `(${summary.coverage_percentage.toFixed(1)}% покрытие)`;

      message.success(successMessage, 8);

      console.log('Автоматическая обработка завершена:', {
        'Время обработки': `${result.processing_time_seconds}с`,
        'Excel записей': summary.total_excel_records,
        'Найдено в БД': summary.products_found_in_db,
        'Покрытие': `${summary.coverage_percentage.toFixed(1)}%`,
        'К производству': summary.production_items_count
      });

      // После успешной обработки сворачиваем промежуточные таблицы
      setTablesCollapsed(prev => ({
        ...prev,
        mergedData: true,
        excelData: true,
        deduplicatedData: true,
        filteredProduction: false // основная таблица результата остается развернутой
      }));
    } catch (error: any) {
      message.error(error.message || 'Ошибка при обработке файла');
    }

    return false; // Предотвращаем автоматическую загрузку
  };

  /**
   * Экспорт дедуплицированных данных Excel
   */
  const handleExportDeduplicatedExcel = async (deduplicatedData: any[]) => {
    if (deduplicatedData.length === 0) {
      message.warning('Нет данных для экспорта');
      return;
    }

    try {
      const result = await dispatch(exportDeduplicated(deduplicatedData)).unwrap();

      // Создаем ссылку для скачивания
      const link = document.createElement('a');
      link.href = result.download_url;
      link.download = 'Данные_Excel_без_дублей.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      message.success('Файл успешно экспортирован');
    } catch (error: any) {
      message.error(error.message || 'Ошибка при экспорте');
    }
  };

  /**
   * Экспорт списка к производству
   */
  const handleExportProductionList = async (filteredData: any[]) => {
    if (filteredData.length === 0) {
      message.warning('Нет данных для экспорта');
      return;
    }

    try {
      const result = await dispatch(exportProduction(filteredData)).unwrap();

      // Создаем ссылку для скачивания
      const link = document.createElement('a');
      link.href = result.download_url;
      link.download = 'Список_к_производству.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Освобождаем URL blob после скачивания
      setTimeout(() => {
        window.URL.revokeObjectURL(result.download_url);
      }, 100);

      message.success('Файл успешно экспортирован');
    } catch (error: any) {
      message.error(error.message || 'Ошибка при экспорте');
    }
  };

  return {
    uploadModalVisible,
    setUploadModalVisible,
    handleExcelUpload,
    handleExportDeduplicatedExcel,
    handleExportProductionList,
    tablesCollapsed,
    setTablesCollapsed,
  };
};
