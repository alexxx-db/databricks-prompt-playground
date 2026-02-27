import { useState } from 'react';
import { ExternalLink, ChevronDown, ChevronUp, Star } from 'lucide-react';
import type { EvalResponse, ScoreDetail } from '../../types';

function ScoreBadge({ score }: { score: number | string | null }) {
  if (score === null || score === undefined) return <span className="text-gray-400 text-xs">–</span>;
  if (typeof score === 'string') {
    // Fraction format "X/Y" from Guidelines judges
    const fractionMatch = score.match(/^(\d+)\/(\d+)$/);
    if (fractionMatch) {
      const num = parseInt(fractionMatch[1]);
      const den = parseInt(fractionMatch[2]);
      const ratio = den > 0 ? num / den : 0;
      const color = ratio === 1 ? 'text-green-600' : ratio >= 0.5 ? 'text-yellow-600' : 'text-red-500';
      return <span className={`font-semibold text-sm ${color}`}>{score} passed</span>;
    }
    const lower = score.toLowerCase();
    const color = ['yes', 'pass', 'true'].includes(lower)
      ? 'text-green-600'
      : ['no', 'fail', 'false'].includes(lower)
        ? 'text-red-500'
        : 'text-blue-600';
    return <span className={`font-semibold text-sm ${color}`}>{score}</span>;
  }
  const color = score >= 4 ? 'text-green-600' : score >= 3 ? 'text-yellow-600' : 'text-red-500';
  return (
    <span className={`font-semibold text-sm flex items-center gap-0.5 ${color}`}>
      <Star className="w-3 h-3 fill-current" />
      {score.toFixed(1)}
    </span>
  );
}

function isPass(value: number | string | null): boolean {
  if (value === null) return false;
  if (typeof value === 'number') return value >= 1;
  return ['true', 'yes', 'pass', '1'].includes(String(value).toLowerCase());
}

function GuidelineChecklist({ details }: { details: ScoreDetail[] }) {
  return (
    <div className="space-y-2">
      {details.map((d, idx) => {
        const pass = isPass(d.value);
        const match = d.name.match(/\/(\d+)$/);
        const label = match ? `Rule ${parseInt(match[1]) + 1}` : d.name;
        return (
          <div key={idx} className="flex gap-2.5 items-start">
            <span className={`mt-0.5 flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold ${
              pass ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
            }`}>
              {pass ? '✓' : '✗'}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-700">{label}</p>
              {d.rationale && (
                <p className="text-[11px] text-gray-500 mt-0.5 leading-relaxed">{d.rationale}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

interface Props {
  result: EvalResponse;
  scorerName?: string | null;
}

export default function EvalResults({ result, scorerName }: Props) {
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      {/* Summary header */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-800">
            {result.prompt_name.split('.').pop()} · v{result.prompt_version} · {result.model_name}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">{result.dataset} · {result.total_rows} rows</p>
        </div>
        <div className="flex items-center gap-4">
          {result.avg_score !== null && (
            <div className="text-center">
              <p className="text-2xl font-bold text-databricks-red">{result.avg_score.toFixed(1)}</p>
              <p className="text-[10px] text-gray-400">avg {scorerName || 'quality'} score</p>
            </div>
          )}
          {result.experiment_url && (
            <a
              href={result.experiment_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-databricks-red hover:underline font-medium"
            >
              <ExternalLink className="w-3 h-3" />
              View in Experiment
            </a>
          )}
        </div>
      </div>

      {/* Per-row results */}
      <div className="space-y-2">
        {result.results.map((row) => (
          <div key={row.row_index} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <button
              onClick={() => setExpandedRow(expandedRow === row.row_index ? null : row.row_index)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors"
            >
              <span className="text-xs text-gray-400 w-6">#{row.row_index + 1}</span>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-600 truncate">
                  {Object.values(row.variables).slice(0, 3).join(' · ')}
                </p>
                {row.score_rationale && (
                  <p className="text-[11px] text-gray-400 truncate mt-0.5">{row.score_rationale}</p>
                )}
              </div>
              <ScoreBadge score={row.score} />
              {expandedRow === row.row_index
                ? <ChevronUp className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                : <ChevronDown className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
              }
            </button>

            {expandedRow === row.row_index && (
              <div className="border-t border-gray-100 px-4 py-3 space-y-3 bg-gray-50">
                <div>
                  <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Variables</p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(row.variables).map(([k, v]) => (
                      <span key={k} className="text-xs bg-white border border-gray-200 rounded px-2 py-0.5">
                        <span className="font-mono text-purple-600">{k}</span>: {v}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Response</p>
                  <p className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">{row.response}</p>
                </div>
                {(row.score_details || row.score_rationale) && (
                  <div>
                    <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Judge Output</p>
                    <div className="bg-white border border-gray-200 rounded-lg p-2.5">
                      {row.score_details && row.score_details.length >= 1 ? (
                        <GuidelineChecklist details={row.score_details} />
                      ) : (
                        <div className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
                          <div className="flex items-center gap-1.5 mb-1">
                            <ScoreBadge score={row.score} />
                          </div>
                          {row.score_rationale}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
