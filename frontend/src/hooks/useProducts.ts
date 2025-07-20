import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { fetchProducts, fetchProductStats } from '../store/products';

export const useProducts = () => {
  const dispatch = useDispatch<AppDispatch>();
  const productsState = useSelector((state: RootState) => state.products);

  useEffect(() => {
    if (!productsState.products.length && !productsState.loading) {
      dispatch(fetchProducts());
    }
    if (!productsState.productStats && !productsState.loading) {
      dispatch(fetchProductStats());
    }
  }, [dispatch, productsState.products.length, productsState.productStats, productsState.loading]);

  return {
    ...productsState,
    refetch: () => {
      dispatch(fetchProducts(productsState.filters));
      dispatch(fetchProductStats());
    }
  };
};