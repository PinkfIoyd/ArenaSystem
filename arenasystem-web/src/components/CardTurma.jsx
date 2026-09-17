import Icon from './Icon';
import { checkinButtonClass, checkinUi } from '../utils/checkinUi';

function CardTurma({
  turma,
  onCheckin,
  onSolicitarMatricula,
  onEntrarFila,
  onSolicitarCancelamento,
  fazendoCheckin,
  processando,
}) {
  const ocupados = turma.vagas - turma.vagas_disponiveis;
  const percentual = turma.vagas > 0 ? (ocupados / turma.vagas) * 100 : 0;

  let corBarra = 'bg-emerald-500';
  if (percentual > 70) corBarra = 'bg-[var(--arena-primary)]';
  if (percentual > 90) corBarra = 'bg-red-500';

  const turmaCheia = turma.vagas_disponiveis === 0;
  const state = fazendoCheckin ? 'requesting' : turma.checkin_state?.state || 'outside_window';
  const checkin = checkinUi(state);

  return (
    <div className="app-surface-hover flex h-full flex-col p-5">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-lg font-bold leading-snug text-slate-950">{turma.nome}</h3>
          <p className="mt-1 text-sm text-slate-500">Prof. {turma.professor_nome}</p>
        </div>
        {turma.matriculado && (
          <span className="shrink-0 rounded-lg bg-emerald-50 px-2.5 py-1.5 text-xs font-bold text-emerald-700">
            Matriculado
          </span>
        )}
      </div>

      <div className="mb-5 space-y-2 text-sm text-slate-600">
        <LinhaInfo icon="pin" label="Quadra" valor={turma.quadra_nome} />
        <LinhaInfo icon="overview" label="Dias" valor={turma.dias_semana} />
        <LinhaInfo icon="queue" label="Horario" valor={turma.horario.slice(0, 5)} />
      </div>

      <div className="mb-5">
        <div className="mb-1 flex justify-between text-xs text-slate-600">
          <span>Vagas</span>
          <span>{ocupados} / {turma.vagas} ocupadas</span>
        </div>
        <div className="h-2 w-full rounded-full bg-slate-200">
          <div
            className={`${corBarra} h-2 rounded-full transition-all`}
            style={{ width: `${percentual}%` }}
          />
        </div>
      </div>

      <div className="mt-auto flex min-h-[108px] flex-col justify-center">
        {turma.matriculado ? (
          <div className="space-y-2">
            <button
              onClick={() => onCheckin(turma.id)}
              disabled={checkin.disabled || fazendoCheckin}
              className={`${checkinButtonClass(state)} w-full rounded-lg py-2.5 font-semibold transition disabled:cursor-not-allowed`}
            >
              {checkin.label}
            </button>
            <button
              onClick={() => onSolicitarCancelamento(turma)}
              disabled={processando}
              className="btn-danger-soft w-full py-2"
            >
              Solicitar cancelamento
            </button>
          </div>
        ) : turmaCheia ? (
          <button
            onClick={() => onEntrarFila(turma)}
            disabled={processando}
            className="btn-secondary w-full py-2.5"
          >
            {processando ? 'Aguarde...' : 'Entrar na fila de espera'}
          </button>
        ) : (
          <button
            onClick={() => onSolicitarMatricula(turma)}
            disabled={processando}
            className="btn-primary w-full py-2.5"
          >
            {processando ? 'Aguarde...' : 'Solicitar matricula'}
          </button>
        )}
      </div>
    </div>
  );
}

function LinhaInfo({ icon, label, valor }) {
  return (
    <p className="flex items-center gap-2">
      <Icon name={icon} className="tenant-link h-4 w-4" />
      <span>
        <strong>{label}:</strong> {valor}
      </span>
    </p>
  );
}

export default CardTurma;
