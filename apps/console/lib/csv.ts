export type CsvField = string | number | boolean | null | undefined;

function escapeField(val: CsvField): string {
  if (val === null || val === undefined) return '';
  const s = String(val);
  // Escape if contains comma, quote, or newline
  if (/[",\n\r]/.test(s)) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

export function toCsv(headers: string[], rows: CsvField[][]): string {
  const head = headers.map(escapeField).join(',');
  const body = rows.map(r => r.map(escapeField).join(',')).join('\n');
  return head + '\n' + body;
}

export function downloadCsv(filenameBase: string, headers: string[], rows: CsvField[][]): void {
  const csv = toCsv(headers, rows);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${filenameBase}_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
