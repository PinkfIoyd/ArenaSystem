function GraficoCard({ titulo, subtitulo, children }) {
  return (
    <div className="app-surface p-5">
      <div className="mb-4">
        <h3 className="font-bold text-slate-950">{titulo}</h3>
        {subtitulo && (
          <p className="text-xs text-slate-500 mt-0.5">{subtitulo}</p>
        )}
      </div>
      <div className="relative" style={{ height: '300px' }}>
        {children}
      </div>
    </div>
  );
}

export default GraficoCard;
