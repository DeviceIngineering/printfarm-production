import { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { fetchSyncStatus, fetchSyncHistory } from '../store/sync';

export const useSync = (pollInterval: number = 2000) => {
  const dispatch = useDispatch<AppDispatch>();
  const syncState = useSelector((state: RootState) => state.sync);
  const intervalRef = useRef<NodeJS.Timer | null>(null);

  useEffect(() => {
    // Initial fetch
    dispatch(fetchSyncStatus());
    dispatch(fetchSyncHistory());

    // Setup polling if syncing
    if (syncState.status?.is_syncing) {
      intervalRef.current = setInterval(() => {
        dispatch(fetchSyncStatus());
      }, pollInterval);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [dispatch, syncState.status?.is_syncing, pollInterval]);

  return syncState;
};