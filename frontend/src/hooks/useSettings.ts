import { useState, useEffect } from 'react';
import { settingsApi, SettingsSummary, SyncSettings, GeneralSettings } from '../api/settings';

export const useSettings = () => {
  const [summary, setSummary] = useState<SettingsSummary | null>(null);
  const [syncSettings, setSyncSettings] = useState<SyncSettings | null>(null);
  const [generalSettings, setGeneralSettings] = useState<GeneralSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = async () => {
    try {
      setError(null);
      const data = await settingsApi.getSettingsSummary();
      setSummary(data);
      setSyncSettings(data.sync_settings);
      setGeneralSettings(data.general_settings);
    } catch (err) {
      setError('Ошибка загрузки настроек');
      console.error('Error loading settings summary:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSyncSettings = async () => {
    try {
      setError(null);
      const data = await settingsApi.getSyncSettings();
      setSyncSettings(data);
    } catch (err) {
      setError('Ошибка загрузки настроек синхронизации');
      console.error('Error loading sync settings:', err);
    }
  };

  const loadGeneralSettings = async () => {
    try {
      setError(null);
      const data = await settingsApi.getGeneralSettings();
      setGeneralSettings(data);
    } catch (err) {
      setError('Ошибка загрузки общих настроек');
      console.error('Error loading general settings:', err);
    }
  };

  const updateSyncSettings = (newSettings: SyncSettings) => {
    setSyncSettings(newSettings);
    if (summary) {
      setSummary({
        ...summary,
        sync_settings: newSettings
      });
    }
  };

  const updateGeneralSettings = (newSettings: GeneralSettings) => {
    setGeneralSettings(newSettings);
    if (summary) {
      setSummary({
        ...summary,
        general_settings: newSettings
      });
    }
  };

  const refresh = () => {
    setLoading(true);
    loadSummary();
  };

  useEffect(() => {
    loadSummary();
  }, []);

  return {
    summary,
    syncSettings,
    generalSettings,
    loading,
    error,
    loadSyncSettings,
    loadGeneralSettings,
    updateSyncSettings,
    updateGeneralSettings,
    refresh
  };
};