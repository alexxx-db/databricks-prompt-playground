import { useState, useEffect, useCallback } from 'react';
import type { ModelEndpoint } from '../types';
import { apiFetch } from './useApi';

export function useModels() {
  const [models, setModels] = useState<ModelEndpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{ models: ModelEndpoint[] }>('/models');
      setModels(data.models);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { models, loading, error, refresh };
}
