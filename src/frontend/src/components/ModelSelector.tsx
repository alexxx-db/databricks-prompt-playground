import { RefreshCw, Cpu } from 'lucide-react';
import type { ModelEndpoint } from '../types';
import SearchableSelect from './SearchableSelect';

interface Props {
  models: ModelEndpoint[];
  loading: boolean;
  error: string | null;
  selectedModel: string | null;
  onSelectModel: (name: string | null) => void;
  onRefresh: () => void;
}

export default function ModelSelector({
  models,
  loading,
  error,
  selectedModel,
  onSelectModel,
  onRefresh,
}: Props) {
  // Filter to show only READY endpoints, but keep all if none are ready
  const readyModels = models.filter((m) => m.state === 'READY');
  const displayModels = readyModels.length > 0 ? readyModels : models;

  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="section-label">Model Endpoint</label>
        <button
          onClick={onRefresh}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="Refresh models"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="mb-2 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</div>
      )}

      <SearchableSelect
        value={selectedModel || ''}
        onChange={(val) => onSelectModel(val || null)}
        disabled={loading}
        placeholder={loading ? 'Loading endpoints...' : 'Select a model...'}
        options={displayModels.map((m) => ({ value: m.name, label: `${m.name} (${m.state})` }))}
        leftIcon={<Cpu className="w-4 h-4 text-gray-400" />}
      />

      {selectedModel && (
        <div className="mt-1.5 text-xs text-gray-500">
          Task:{' '}
          {displayModels.find((m) => m.name === selectedModel)?.task || 'unknown'}
        </div>
      )}
    </div>
  );
}
