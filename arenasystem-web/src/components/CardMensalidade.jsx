import Badge from './Badge';
import {
  formatarMoeda,
  formatarData,
  formatarMesAno,
  diasAteVencimento,
} from '../utils/format';

function CardMensalidade({ mensalidade, onPagar }) {
  const dias = diasAteVencimento(mensalidade.vencimento);

  let alerta = null;
  if ((mensalidade.status === 'pendente' || mensalidade.status === 'atrasado') && dias !== null) {
    if (dias < 0) {
      alerta = (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">
          Vencida ha {Math.abs(dias)} dia{Math.abs(dias) !== 1 ? 's' : ''}
          {mensalidade.status === 'pendente' ? ' (fica atrasada no 5o dia)' : ''}
        </p>
      );
    } else if (dias === 0) {
      alerta = (
        <p className="mt-3 rounded-lg bg-cyan-50 px-3 py-2 text-xs font-semibold text-cyan-700">
          Vence hoje
        </p>
      );
    } else if (dias <= 5) {
      alerta = (
        <p className="mt-3 rounded-lg bg-cyan-50 px-3 py-2 text-xs font-semibold text-cyan-700">
          Vence em {dias} dia{dias !== 1 ? 's' : ''}
        </p>
      );
    }
  }

  return (
    <div className="app-surface-hover p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="page-kicker">Mensalidade</p>
          <h3 className="mt-1 text-xl font-bold capitalize text-slate-950">
            {formatarMesAno(mensalidade.mes_referencia)}
          </h3>
          <p className="mt-1 text-sm text-slate-500">{mensalidade.plano_nome}</p>
        </div>
        <Badge status={mensalidade.status} texto={mensalidade.status_display} />
      </div>

      <div className="space-y-2 border-t border-slate-100 pt-4 text-sm">
        <Linha label="Valor" value={formatarMoeda(mensalidade.valor)} destaque />
        <Linha label="Vencimento" value={formatarData(mensalidade.vencimento)} />
        {mensalidade.data_pagamento && (
          <Linha label="Pago em" value={formatarData(mensalidade.data_pagamento)} sucesso />
        )}
      </div>

      {alerta}

      {(mensalidade.status === 'pendente' || mensalidade.status === 'atrasado') && (
        <button
          onClick={() => onPagar(mensalidade)}
          className="btn-success mt-4 w-full"
        >
          Pagar pelo Mercado Pago
        </button>
      )}
    </div>
  );
}

function Linha({ label, value, destaque = false, sucesso = false }) {
  return (
    <div className="flex justify-between gap-3">
      <span className="text-slate-500">{label}:</span>
      <span className={`${destaque ? 'text-lg font-bold text-slate-950' : sucesso ? 'font-semibold text-emerald-700' : 'text-slate-800'}`}>
        {value}
      </span>
    </div>
  );
}

export default CardMensalidade;
