import { Play, Settings2, RotateCcw } from 'lucide-react';
import { useState } from 'react';

interface Props {
  canRun: boolean;
  loading: boolean;
  onRun: (params: { max_tokens: number; temperature: number }) => void;
  onReset: () => void;
}

export default function RunControls({ canRun, loading, onRun, onReset }: Props) {
  const [showSettings, setShowSettings] = useState(false);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [temperature, setTemperature] = useState(1.0);

  return (
    <div className="space-y-3">
      {/* Advanced settings toggle */}
      <button
        onClick={() => setShowSettings(!showSettings)}
        className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors"
      >
        <Settings2 className="w-3.5 h-3.5" />
        <span>{showSettings ? 'Hide' : 'Show'} settings</span>
      </button>

      {showSettings && (
        <div className="space-y-3 p-3 bg-gray-50 rounded-lg">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-gray-600">
                Max Tokens
              </label>
              <span className="text-xs text-gray-500">{maxTokens}</span>
            </div>
            <input
              type="range"
              min={256}
              max={16384}
              step={256}
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
              className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-databricks-red"
            />
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-medium text-gray-600">
                Temperature
              </label>
              <span className="text-xs text-gray-500">{temperature.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-databricks-red"
            />
          </div>
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => onRun({ max_tokens: maxTokens, temperature })}
          disabled={!canRun || loading}
          className="btn-primary flex-1"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Run Prompt
            </>
          )}
        </button>
        <button
          onClick={onReset}
          className="btn-secondary"
          title="Reset response"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
