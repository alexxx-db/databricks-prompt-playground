import { useState, useCallback } from 'react';
import type { RunResponse } from '../types';
import { apiFetch, useMutation } from './useApi';

export function useRunPrompt() {
  const [result, setResult] = useState<RunResponse | null>(null);

  const { mutate, loading, error } = useMutation(
    async (params: {
      prompt_name: string;
      prompt_version: string;
      variables: Record<string, string>;
      model_name: string;
      max_tokens?: number;
      temperature?: number;
      experiment_name?: string;
      draft_template?: string;
    }) => {
      setResult(null);
      const data = await apiFetch<RunResponse>('/run', {
        method: 'POST',
        body: JSON.stringify(params),
      });
      setResult(data);
      return data;
    }
  );

  const reset = useCallback(() => {
    setResult(null);
  }, []);

  return { result, loading, error, run: mutate, reset };
}
