function KpiCard({ titulo, valor, sublabel, subtitulo, icone, cor = 'arena' }) {
  const cores = {
    arena: 'bg-cyan-50 text-teal-800',
    green: 'bg-emerald-50 text-emerald-700',
    red: 'bg-red-50 text-red-700',
    blue: 'bg-sky-50 text-sky-700',
    purple: 'bg-violet-50 text-violet-700',
    cyan: 'bg-cyan-50 text-cyan-700',
  };

  return (
    <div className="metric-card transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-500 uppercase tracking-wide font-bold">
            {titulo}
          </p>
          <p className="text-2xl font-bold mt-1 text-slate-950 truncate">
            {valor}
          </p>
          {(sublabel || subtitulo) && (
            <p className="text-xs text-slate-500 mt-1">{sublabel || subtitulo}</p>
          )}
        </div>
        <div className={`ml-2 grid h-12 w-12 shrink-0 place-items-center rounded-xl ${cores[cor] || cores.arena}`}>
          {icone}
        </div>
      </div>
    </div>
  );
}

export default KpiCard;
