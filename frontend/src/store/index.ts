import { configureStore } from '@reduxjs/toolkit';
import { productsReducer } from './products';
import { syncReducer } from './sync';
import { tochkaReducer } from './tochka';

export const store = configureStore({
  reducer: {
    products: productsReducer,
    sync: syncReducer,
    tochka: tochkaReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;