import { formatCurrency, formatNumber, toTitleCase } from '../lib/formatters';

function renderCell(value, column) {
  if (value === null || value === undefined || value === '') return '-';
  if (column.currency) return formatCurrency(value);
  if (column.numeric) return formatNumber(value);
  return String(value);
}

export function DataTable({ rows = [], columns = [], emptyMessage = 'No records available.' }) {
  if (!rows.length) {
    return (
      <div className="table-shell p-8 text-center text-sm text-muted">
        {emptyMessage}
      </div>
    );
  }

  const resolvedColumns =
    columns.length > 0
      ? columns
      : Object.keys(rows[0] || {})
          .filter((key) => key !== 'id' && key !== 'raw')
          .map((key) => ({ key, label: toTitleCase(key) }));

  return (
    <div className="table-shell overflow-x-auto">
      <table className="min-w-full divide-y divide-line text-sm">
        <thead className="sticky top-0 z-10 bg-[#0f172a]/95 backdrop-blur">
          <tr>
            {resolvedColumns.map((column) => (
              <th key={column.key} className="whitespace-nowrap px-5 py-4 text-left font-semibold text-muted">
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line bg-surface/95">
          {rows.map((row, index) => (
            <tr
              key={row.id || row.symbol || row.year || row.quarter}
              className={index % 2 === 0 ? 'bg-white/[0.01] transition hover:bg-white/[0.05]' : 'bg-white/[0.035] transition hover:bg-white/[0.06]'}
            >
              {resolvedColumns.map((column) => (
                <td key={column.key} className="whitespace-nowrap px-5 py-4 text-ink">
                  {renderCell(row[column.key], column)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
