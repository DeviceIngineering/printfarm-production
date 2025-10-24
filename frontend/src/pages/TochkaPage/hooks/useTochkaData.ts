/**
 * Hook для управления данными TochkaPage
 * Инкапсулирует логику загрузки данных из Redux и обработки ошибок
 */
import { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { message } from 'antd';
import { RootState } from '../../../store';
import { AppDispatch } from '../../../store';
import {
  fetchTochkaProducts,
  fetchTochkaProduction,
  clearError,
} from '../../../store/tochka';

export const useTochkaData = () => {
  const dispatch = useDispatch<AppDispatch>();

  // Получаем данные из Redux store
  const {
    products: productsData,
    production: productionData,
    excelData,
    deduplicatedExcelData,
    mergedData,
    filteredProductionData,
    coverage,
    productionStats,
    loading,
    error
  } = useSelector((state: RootState) => state.tochka);

  /**
   * Загрузка товаров
   */
  const loadProducts = async () => {
    try {
      await dispatch(fetchTochkaProducts()).unwrap();
      message.success('Товары загружены');
    } catch (error) {
      message.error('Ошибка загрузки товаров');
    }
  };

  /**
   * Загрузка списка на производство
   */
  const loadProductionList = async () => {
    try {
      await dispatch(fetchTochkaProduction()).unwrap();
      message.success('Список на производство загружен');
    } catch (error) {
      message.error('Ошибка загрузки списка на производство');
    }
  };

  /**
   * Загрузка данных при монтировании только если они отсутствуют
   */
  useEffect(() => {
    if (productsData.length === 0) {
      loadProducts();
    }
  }, []);

  /**
   * Очистка ошибок при размонтировании
   */
  useEffect(() => {
    return () => {
      if (error) {
        dispatch(clearError());
      }
    };
  }, [dispatch, error]);

  return {
    // Данные
    productsData,
    productionData,
    excelData,
    deduplicatedExcelData,
    mergedData,
    filteredProductionData,
    coverage,
    productionStats,
    loading,
    error,

    // Методы
    loadProducts,
    loadProductionList,
  };
};
