const ARTICLES = [
  ['Primeiros passos', 'Use o onboarding para configurar identificacao, horarios, quadras, modalidades, professores e a importacao inicial de alunos.'],
  ['Equipe e acessos', 'Convide cada pessoa pelo proprio e-mail. O proprietario pode transferir a conta, desativar acessos e revisar os perfis.'],
  ['Assinatura e limites', 'Minha assinatura mostra consumo, plano e cobrancas. Upgrades dependem do pagamento; downgrades entram no proximo ciclo.'],
  ['Suporte', 'Abra um chamado informando impacto e prioridade. Respostas e o prazo de SLA aparecem no historico do ticket.'],
  ['Privacidade', 'Use a area Privacidade para exportacao, correcao, exclusao ou anonimizacao. Solicitacoes destrutivas passam por revisao.'],
];

function Ajuda() {
  return <div className="mx-auto max-w-4xl space-y-6"><header><p className="muted-label">Central de ajuda</p><h1 className="text-3xl font-bold">Como usar o ArenaFlow</h1><p className="mt-2 text-slate-600">Guias curtos para as principais rotinas administrativas.</p></header><div className="space-y-3">{ARTICLES.map(([title, content]) => <details key={title} className="app-surface p-5"><summary className="cursor-pointer text-lg font-bold">{title}</summary><p className="mt-3 leading-relaxed text-slate-600">{content}</p></details>)}</div></div>;
}
export default Ajuda;

