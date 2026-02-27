import { Variable } from 'lucide-react';

interface Props {
  variables: string[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
}

export default function VariableInputs({ variables, values, onChange }: Props) {
  if (variables.length === 0) return null;

  return (
    <div>
      <label className="section-label">Template Variables</label>
      <div className="space-y-3">
        {variables.map((varName) => (
          <div key={varName}>
            <div className="flex items-center gap-1.5 mb-1">
              <Variable className="w-3 h-3 text-databricks-red" />
              <label
                htmlFor={`var-${varName}`}
                className="text-sm font-medium text-gray-700"
              >
                {varName}
              </label>
            </div>
            <textarea
              id={`var-${varName}`}
              className="input-field resize-none"
              rows={2}
              placeholder={`Enter value for {{${varName}}}`}
              value={values[varName] || ''}
              onChange={(e) => onChange(varName, e.target.value)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
