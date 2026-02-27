/**
 * Extract {{variable}} patterns from a template string, preserving order.
 * Matches the backend's parse_template_variables() logic.
 */
export function parseTemplateVariables(template: string): string[] {
  const matches = template.matchAll(/\{\{(\s*\w+\s*)\}\}/g);
  const seen = new Set<string>();
  const vars: string[] = [];
  for (const m of matches) {
    const v = m[1].trim();
    if (!seen.has(v)) {
      seen.add(v);
      vars.push(v);
    }
  }
  return vars;
}
