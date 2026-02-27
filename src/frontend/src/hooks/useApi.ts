/**
 * Shared API utilities and re-exports.
 *
 * apiFetch and useMutation are the building blocks used by all domain-specific hook files.
 * All hooks are re-exported here so existing imports continue to work.
 */

import { useState, useEffect, useCallback } from 'react';
import type { AppConfig } from '../types';

const API_BASE = '/api';

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `API error: ${res.status}`);
  }
  return res.json();
}

/**
 * Generic hook for POST/mutation API calls.
 * Handles loading state, error capture, and re-throw.
 */
export function useMutation<TParams, TResult>(
  fn: (params: TParams) => Promise<TResult>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutate = useCallback(
    async (params: TParams): Promise<TResult> => {
      setLoading(true);
      setError(null);
      try {
        const data = await fn(params);
        return data;
      } catch (e: any) {
        setError(e.message);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [fn]
  );

  return { mutate, loading, error };
}

// --- Config ---

export function useConfig() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<AppConfig>('/config')
      .then((data) => setConfig(data))
      .catch(() =>
        setConfig({ prompt_catalog: 'main', prompt_schema: 'prompts', eval_catalog: 'main', eval_schema: 'eval_data', mlflow_experiment_name: '/Shared/prompt-playground-evaluation' })
      )
      .finally(() => setLoading(false));
  }, []);

  return { config, loading };
}

// --- Re-exports for backward compatibility ---

export { usePrompts, usePromptVersions, usePromptTemplate, useCreatePrompt, useSaveVersion } from './usePromptApi';
export { useModels } from './useModelApi';
export { useRunPrompt } from './useRunApi';
export { useExperiments, useExperimentPrompts, useJudges, useCreateJudge, useDeleteJudge, useEvalTables, useEvalColumns, useRunEval } from './useEvalApi';
