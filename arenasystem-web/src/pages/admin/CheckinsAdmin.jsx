import { useState } from 'react';
import AccessQueue from '../../components/AccessQueue';
import CheckinQueue from '../../components/CheckinQueue';
import useTerminology from '../../hooks/useTerminology';

export default function CheckinsAdmin() {
  const { features } = useTerminology();
  const initial = features.classes ? 'classes' : 'access';
  const [tab, setTab] = useState(initial);
  const tabs = [
    ...(features.classes ? [{ id: 'classes', label: 'Aulas' }] : []),
    ...(features.openAccess ? [{ id: 'access', label: 'Acesso livre' }] : []),
  ];
  const active = tabs.some((item) => item.id === tab) ? tab : tabs[0]?.id;

  return <div>
    <p className="page-kicker">Operação do dia</p>
    <h1 className="page-title">Validação de entradas</h1>
    <p className="page-subtitle mb-5">Filas atualizadas automaticamente a cada cinco segundos.</p>
    {tabs.length > 1 && <div className="mb-6 inline-flex rounded-xl bg-slate-100 p-1">{tabs.map((item) => <button type="button" key={item.id} onClick={() => setTab(item.id)} className={`rounded-lg px-5 py-2 text-sm font-black ${active === item.id ? 'bg-white text-slate-950 shadow-sm' : 'text-slate-500'}`}>{item.label}</button>)}</div>}
    {active === 'classes' && <CheckinQueue showSettings />}
    {active === 'access' && <AccessQueue />}
  </div>;
}
