import { forcaSenha } from '../utils/validacao';

function IndicadorForcaSenha({ senha }) {
  if (!senha) return null;

  const forca = forcaSenha(senha);
  const niveis = [
    { texto: 'Muito fraca', cor: 'bg-red-500' },
    { texto: 'Fraca', cor: 'bg-rose-500' },
    { texto: 'Regular', cor: 'bg-cyan-500' },
    { texto: 'Boa', cor: 'bg-sky-500' },
    { texto: 'Forte', cor: 'bg-emerald-500' },
  ];

  return (
    <div className="mt-2">
      <div className="flex gap-1 mb-1">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded ${
              i < forca ? niveis[forca].cor : 'bg-slate-200'
            }`}
          />
        ))}
      </div>
      <p className={`text-xs ${
        forca <= 1 ? 'text-red-600' :
        forca <= 2 ? 'text-cyan-700' :
        'text-emerald-600'
      }`}>
        {niveis[forca].texto}
      </p>
    </div>
  );
}

export default IndicadorForcaSenha;
