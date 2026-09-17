import Layout from '../components/Layout';
import CheckinQueue from '../components/CheckinQueue';

export default function ProfessorCheckins() {
  return <Layout><div className="mx-auto max-w-5xl"><p className="page-kicker">Professor</p><h1 className="page-title">Aulas e presenças de hoje</h1><p className="page-subtitle mb-6">Você visualiza e valida somente alunos das suas próprias turmas.</p><CheckinQueue /></div></Layout>;
}
