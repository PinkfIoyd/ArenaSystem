function ResumoCard({ titulo, valor, cor = 'arena', icone }) {
  const cores = {
    arena: 'bg-cyan-50 text-teal-800',
    green: 'bg-emerald-50 text-emerald-700',
    red: 'bg-red-50 text-red-700',
    blue: 'bg-sky-50 text-sky-700',
    cyan: 'bg-cyan-50 text-cyan-700',
    gray: 'bg-slate-50 text-slate-700',
  };

  const classeCor = cores[cor] || cores.arena;

  return (
    <div className="metric-card">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{titulo}</p>
          <p className="mt-1 truncate text-2xl font-bold text-slate-950">{valor}</p>
        </div>
        <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl text-lg font-bold ${classeCor}`}>
          {icone}
        </div>
      </div>
    </div>
  );
}

export default ResumoCard;
