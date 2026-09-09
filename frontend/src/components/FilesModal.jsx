import { useState, useRef, useEffect } from 'react';
import { useI18n } from '../context/I18nContext';

// Mock data — estos reportes vendrán del backend (storage/reports) más adelante
const MOCK_FILES = [
  { id: 1, name: 'resumen_ventas_por_cliente', type: 'md', size: '24 KB', date: '2026-07-30 18:22', conversation: 'New Database Chat', content: '# Resumen de ventas por cliente\n\n## Top 5 clientes\n\n| Cliente | Ventas | Órdenes |\n|---------|--------|---------|\n| Constructora MX | $1,240,500 | 48 |\n| Edificaciones del Norte | $980,300 | 37 |\n| Inmobiliaria Central | $875,200 | 31 |\n| Desarrollo Urbano SA | $720,900 | 25 |\n| Casas y Más | $510,800 | 19 |\n\n## Conclusiones\n\n- El cliente más rentable es **Constructora MX** con 48 órdenes.\n- Las ventas crecieron un 12% respecto al trimestre anterior.' },
  { id: 2, name: 'inventario_materiales_bajo_stock', type: 'xlsx', size: '18 KB', date: '2026-07-30 17:05', conversation: 'New Database Chat' },
  { id: 3, name: 'proyectos_activos_por_estado', type: 'csv', size: '9 KB', date: '2026-07-29 14:40', conversation: 'New Database Chat', content: 'proyecto,estado,presupuesto,progreso\nTorre Altura,En ejecución,$4,500,000,65%\nPlaza Comercial Centro,En ejecución,$2,800,000,40%\nResidencial Bosque,Planificación,$6,200,000,5%\nPuente Norte,Finalizado,$1,900,000,100%\nOficinas Reforma,En ejecución,$3,400,000,78%' },
  { id: 4, name: 'reporte_presupuesto_trimestral', type: 'pdf', size: '156 KB', date: '2026-07-28 09:15', conversation: 'New Database Chat' },
  { id: 5, name: 'empleados_por_departamento', type: 'html', size: '32 KB', date: '2026-07-27 16:30', conversation: 'New Database Chat', content: '<h1>Empleados por departamento</h1><table border="1"><tr><th>Departamento</th><th>Empleados</th></tr><tr><td>Construcción</td><td>45</td></tr><tr><td>Ingeniería</td><td>28</td></tr><tr><td>Administración</td><td>15</td></tr></table>' },
  { id: 6, name: 'ordenes_pendientes_entrega', type: 'csv', size: '6 KB', date: '2026-07-26 11:45', conversation: 'New Database Chat', content: 'orden,cliente,fecha_entrega,estado\nORD-1042,Constructora MX,2026-08-01,Pendiente\nORD-1043,Edificaciones del Norte,2026-08-03,Pendiente\nORD-1044,Inmobiliaria Central,2026-08-05,En proceso' },
  { id: 7, name: 'analisis_costos_por_proyecto', type: 'md', date: '2026-07-25 10:00', conversation: 'New Database Chat', content: '# Análisis de costos por proyecto\n\n## Costos acumulados\n\n1. **Torre Altura**: $2,900,000 (65% avance)\n2. **Plaza Comercial**: $1,120,000 (40% avance)\n3. **Oficinas Reforma**: $2,650,000 (78% avance)\n\n> Los costos están dentro del presupuesto estimado.' },
  { id: 8, name: 'reporte_ventas_mensual', type: 'xlsx', size: '21 KB', date: '2026-07-24 15:20', conversation: 'New Database Chat' },
];

const TYPE_ICONS = {
  md: 'description',
  xlsx: 'table_chart',
  csv: 'grid_on',
  pdf: 'picture_as_pdf',
  html: 'code',
};

const TYPE_COLORS = {
  md: '#0891b2', xlsx: '#16a34a', csv: '#f59e0b', pdf: '#ef4444', html: '#8b5cf6',
};

const TYPE_LABELS = { md: 'MD', xlsx: 'XLSX', csv: 'CSV', pdf: 'PDF', html: 'HTML' };

const FILTERS = ['all', 'md', 'xlsx', 'csv', 'pdf', 'html'];

export default function FilesModal({ onClose }) {
  const { t } = useI18n();
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const modalRef = useRef();

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const close = (e) => { if (e.target === modalRef.current) onClose(); };

  const files = MOCK_FILES.filter(f => {
    const matchesQuery = f.name.toLowerCase().includes(query.toLowerCase());
    const matchesFilter = filter === 'all' || f.type === filter;
    return matchesQuery && matchesFilter;
  });

  const openPreview = (f) => {
    setSelected(f);
    setPreviewOpen(true);
  };

  const isTextPreview = (type) => ['md', 'csv', 'html'].includes(type);

  const formatDate = (d) => d;

  return (
    <div ref={modalRef} onClick={close}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="mx-4 flex h-[85vh] w-full max-w-3xl flex-col rounded-2xl border shadow-2xl"
        style={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}>
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b px-6 py-4" style={{ borderColor: 'var(--color-border)' }}>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined" style={{ color: 'var(--color-primary)' }}>folder_open</span>
            <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text)' }}>Files</h2>
            <span className="rounded-full px-2 py-0.5 text-xs" style={{ backgroundColor: 'var(--color-page)', color: 'var(--color-text-muted)' }}>
              {files.length} {files.length === 1 ? 'file' : 'files'}
            </span>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 transition hover:bg-page" style={{ color: 'var(--color-text-muted)' }}>
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Search + filter tabs */}
        <div className="shrink-0 border-b px-6 py-4" style={{ borderColor: 'var(--color-border)' }}>
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-lg" style={{ color: 'var(--color-text-muted)' }}>search</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search files..."
              className="w-full rounded-xl border px-10 py-2.5 text-sm outline-none focus:ring-2"
              style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-page)', color: 'var(--color-text)' }}
            />
            {query && (
              <button onClick={() => setQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }}>
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            )}
          </div>
          <div className="mt-3 flex gap-1.5">
            {FILTERS.map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${filter === f ? 'btn-active' : 'btn-inactive'}`}>
                {f === 'all' ? 'All' : TYPE_LABELS[f]}
              </button>
            ))}
          </div>
        </div>

        {/* File list */}
        <div className="flex-1 overflow-y-auto p-4">
          {files.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center py-16">
              <span className="material-symbols-outlined text-5xl mb-3" style={{ color: 'var(--color-text-muted)' }}>folder_off</span>
              <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>No files found</p>
            </div>
          ) : (
            <div className="space-y-1.5">
              {files.map(f => (
                <div key={f.id}
                  onClick={() => openPreview(f)}
                  className="flex cursor-pointer items-center justify-between rounded-xl border px-4 py-3 transition hover:opacity-80"
                  style={{ borderColor: 'var(--color-border)' }}>
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
                      style={{ backgroundColor: `${TYPE_COLORS[f.type]}1a`, color: TYPE_COLORS[f.type] }}>
                      <span className="material-symbols-outlined text-lg">{TYPE_ICONS[f.type]}</span>
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium" style={{ color: 'var(--color-text)' }}>{f.name}.{f.type}</p>
                      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{formatDate(f.date)}{f.size ? ` · ${f.size}` : ''}</p>
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5 ml-3">
                    {isTextPreview(f.type) && (
                      <button onClick={(e) => { e.stopPropagation(); openPreview(f); }}
                        className="rounded-lg p-2 transition hover:bg-page" style={{ color: 'var(--color-text-muted)' }}
                        title="Preview">
                        <span className="material-symbols-outlined text-lg">visibility</span>
                      </button>
                    )}
                    <button onClick={(e) => { e.stopPropagation(); window.open(`#download-${f.name}`, '_blank'); }}
                      className="rounded-lg p-2 transition hover:bg-page" style={{ color: 'var(--color-text-muted)' }}
                      title="Open in new tab">
                      <span className="material-symbols-outlined text-lg">open_in_new</span>
                    </button>
                    <button onClick={(e) => { e.stopPropagation(); }}
                      className="rounded-lg px-2.5 py-1.5 text-xs font-medium btn-active"
                      title="Download">
                      <span className="material-symbols-outlined text-sm align-middle">download</span>
                      Download
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Preview panel (inline) */}
        {previewOpen && selected && (
          <div className="shrink-0 border-t p-4" style={{ borderColor: 'var(--color-border)' }}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text)' }}>
                <span className="material-symbols-outlined text-base align-middle mr-1" style={{ color: TYPE_COLORS[selected.type] }}>{TYPE_ICONS[selected.type]}</span>
                {selected.name}.{selected.type}
              </p>
              <button onClick={() => setPreviewOpen(false)} className="rounded-lg p-1 transition hover:bg-page" style={{ color: 'var(--color-text-muted)' }}>
                <span className="material-symbols-outlined text-lg">expand_more</span>
              </button>
            </div>
            <div className="max-h-48 overflow-y-auto rounded-xl border p-4 font-mono text-xs whitespace-pre-wrap"
              style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-page)', color: 'var(--color-text-muted)' }}>
              {selected.type === 'html'
                ? <div dangerouslySetInnerHTML={{ __html: selected.content }} style={{ fontFamily: 'inherit' }} />
                : selected.content}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
