import { useEffect, useMemo, useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { clearArenaContext } from '../arena/contextStorage';
import IndicadorForcaSenha from '../components/IndicadorForcaSenha';
import Icon from '../components/Icon';
import {
  validarEmail,
  validarCPF,
  formatarCPF,
  formatarTelefone,
  forcaSenha,
} from '../utils/validacao';

function Cadastro() {
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    username: '',
    email: '',
    cpf: '',
    telefone: '',
    data_nascimento: '',
    arena_slug: '',
    password: '',
    password_confirm: '',
  });

  const [arenas, setArenas] = useState([]);
  const [carregandoArenas, setCarregandoArenas] = useState(true);
  const [erros, setErros] = useState({});
  const [erroGeral, setErroGeral] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    let active = true;

    async function carregarArenas() {
      setCarregandoArenas(true);
      try {
        const { data } = await api.get('/arenas/publicas/');
        const lista = Array.isArray(data) ? data : data.results || [];
        if (!active) return;
        setArenas(lista);

        const arenaUrl = searchParams.get('arena');
        const arenaInicial = lista.find((arena) => arena.slug === arenaUrl);
        if (arenaInicial) {
          setForm((atual) => ({ ...atual, arena_slug: arenaInicial.slug }));
        }
      } catch {
        if (active) setErroGeral('Nao foi possivel carregar as arenas disponiveis.');
      } finally {
        if (active) setCarregandoArenas(false);
      }
    }

    void carregarArenas();

    return () => {
      active = false;
    };
  }, [searchParams]);

  const arenaSelecionada = useMemo(
    () => arenas.find((arena) => arena.slug === form.arena_slug),
    [arenas, form.arena_slug],
  );

  const handleChange = (campo, valor) => {
    setForm((atual) => ({ ...atual, [campo]: valor }));
    if (erros[campo]) {
      setErros((atual) => ({ ...atual, [campo]: null }));
    }
  };

  const validarFormulario = () => {
    const novosErros = {};

    if (!form.first_name.trim()) novosErros.first_name = 'Informe seu nome';
    if (!form.last_name.trim()) novosErros.last_name = 'Informe seu sobrenome';
    if (!form.arena_slug) novosErros.arena_slug = 'Selecione a arena onde voce quer se matricular';

    if (!form.username.trim()) {
      novosErros.username = 'Escolha um nome de usuario';
    } else if (form.username.length < 3) {
      novosErros.username = 'Minimo de 3 caracteres';
    } else if (!/^[a-zA-Z0-9_]+$/.test(form.username)) {
      novosErros.username = 'Use apenas letras, numeros e _';
    }

    if (!form.email.trim()) {
      novosErros.email = 'Informe seu e-mail';
    } else if (!validarEmail(form.email)) {
      novosErros.email = 'E-mail invalido';
    }

    if (form.cpf && !validarCPF(form.cpf)) {
      novosErros.cpf = 'CPF invalido';
    }

    if (!form.password) {
      novosErros.password = 'Crie uma senha';
    } else if (forcaSenha(form.password) < 2) {
      novosErros.password = 'Senha muito fraca. Use letras, numeros e simbolos';
    }

    if (form.password !== form.password_confirm) {
      novosErros.password_confirm = 'As senhas nao coincidem';
    }

    setErros(novosErros);
    return Object.keys(novosErros).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErroGeral('');

    if (!validarFormulario()) return;

    setEnviando(true);
    try {
      await api.post('/auth/register/', {
        ...form,
        cpf: form.cpf.replace(/\D/g, ''),
        telefone: form.telefone.replace(/\D/g, ''),
      });

      const { data: tokens } = await api.post('/auth/login/', {
        username: form.username,
        password: form.password,
      });

      clearArenaContext();
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);

      setSucesso(true);
      setTimeout(() => navigate('/'), 1200);
    } catch (err) {
      const dados = err.response?.data;

      if (dados && typeof dados === 'object') {
        const errosCampo = {};
        Object.entries(dados).forEach(([campo, mensagens]) => {
          if (Array.isArray(mensagens)) {
            errosCampo[campo] = mensagens[0];
          } else if (typeof mensagens === 'string') {
            errosCampo[campo] = mensagens;
          }
        });
        setErros(errosCampo);

        if (dados.detail || dados.non_field_errors) {
          setErroGeral(dados.detail || dados.non_field_errors[0]);
        }
      } else {
        setErroGeral('Erro ao realizar cadastro. Tente novamente.');
      }
    } finally {
      setEnviando(false);
    }
  };

  if (sucesso) {
    return (
      <div className="app-shell-bg flex min-h-screen items-center justify-center px-4">
        <div className="app-surface w-full max-w-md p-8 text-center">
          <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-lg bg-emerald-50 text-emerald-700">
            <Icon name="check" className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-bold text-slate-950">Cadastro realizado</h1>
          <p className="mt-2 text-slate-600">
            Bem-vindo{arenaSelecionada ? ` a ${arenaSelecionada.nome}` : ''}. Redirecionando...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell-bg min-h-screen px-4 py-8">
      <div className="mx-auto grid w-full max-w-6xl gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <aside className="rounded-lg border border-cyan-100 bg-slate-950 p-8 text-white">
          <div className="flex items-center gap-3 text-2xl font-bold">
            <span className="grid h-11 w-11 place-items-center rounded-lg bg-white/10">
              <Icon name="court" className="h-6 w-6" />
            </span>
            ArenaFlow
          </div>
          <div className="mt-12">
            <p className="text-xs font-bold uppercase tracking-wide text-emerald-300">Conta do aluno</p>
            <h1 className="mt-3 text-4xl font-bold leading-tight">Entre na rotina digital da arena.</h1>
            <p className="mt-4 text-sm leading-6 text-slate-200">
              Acompanhe turmas, mensalidades, reservas e pedidos com uma experiencia simples para o aluno e organizada para a gestao.
            </p>
          </div>
        </aside>

        <main className="app-surface p-6 md:p-8">
          <div className="mb-6">
            <p className="page-kicker">Cadastro</p>
            <h2 className="page-title">Criar conta</h2>
            <p className="page-subtitle">Escolha sua arena e preencha seus dados para acessar o app do aluno.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <CampoSelect
              label="Arena *"
              valor={form.arena_slug}
              onChange={(v) => handleChange('arena_slug', v)}
              erro={erros.arena_slug}
              carregando={carregandoArenas}
              opcoes={arenas}
            />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Campo label="Nome *" valor={form.first_name} onChange={(v) => handleChange('first_name', v)} erro={erros.first_name} placeholder="Joao" />
              <Campo label="Sobrenome *" valor={form.last_name} onChange={(v) => handleChange('last_name', v)} erro={erros.last_name} placeholder="Silva" />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Campo label="Usuario *" valor={form.username} onChange={(v) => handleChange('username', v.toLowerCase())} erro={erros.username} placeholder="joaosilva" dica="Use letras, numeros e _" />
              <Campo label="E-mail *" tipo="email" valor={form.email} onChange={(v) => handleChange('email', v)} erro={erros.email} placeholder="joao@email.com" />
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Campo label="CPF" valor={form.cpf} onChange={(v) => handleChange('cpf', formatarCPF(v))} erro={erros.cpf} placeholder="000.000.000-00" />
              <Campo label="Telefone" valor={form.telefone} onChange={(v) => handleChange('telefone', formatarTelefone(v))} erro={erros.telefone} placeholder="(11) 99999-9999" />
            </div>

            <Campo label="Data de nascimento" tipo="date" valor={form.data_nascimento} onChange={(v) => handleChange('data_nascimento', v)} erro={erros.data_nascimento} />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <Campo label="Senha *" tipo="password" valor={form.password} onChange={(v) => handleChange('password', v)} erro={erros.password} placeholder="Minimo 8 caracteres" />
                <IndicadorForcaSenha senha={form.password} />
              </div>
              <Campo label="Confirmar senha *" tipo="password" valor={form.password_confirm} onChange={(v) => handleChange('password_confirm', v)} erro={erros.password_confirm} placeholder="Digite a senha novamente" />
            </div>

            {erroGeral && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm font-semibold text-red-700">
                {erroGeral}
              </div>
            )}

            <button type="submit" disabled={enviando || carregandoArenas} className="btn-primary mt-3 w-full py-3">
              {enviando ? 'Criando conta...' : 'Criar conta'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Ja tem conta?{' '}
            <Link to="/login" className="font-semibold text-teal-800 hover:underline">
              Fazer login
            </Link>
          </p>
        </main>
      </div>
    </div>
  );
}

function CampoSelect({ label, valor, onChange, erro, carregando, opcoes }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-semibold text-slate-700">{label}</span>
      <select
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        disabled={carregando}
        className={`field-control ${erro ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''}`}
      >
        <option value="">{carregando ? 'Carregando arenas...' : 'Selecione a arena'}</option>
        {opcoes.map((arena) => (
          <option key={arena.id} value={arena.slug}>
            {arena.nome}
          </option>
        ))}
      </select>
      {erro && <p className="mt-1 text-xs font-semibold text-red-600">{erro}</p>}
      {!erro && !carregando && opcoes.length === 0 && (
        <p className="mt-1 text-xs font-semibold text-red-600">Nenhuma arena ativa disponivel para cadastro.</p>
      )}
    </label>
  );
}

function Campo({ label, tipo = 'text', valor, onChange, erro, placeholder, dica }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-semibold text-slate-700">{label}</span>
      <input
        type={tipo}
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`field-control ${erro ? 'border-red-400 focus:border-red-400 focus:ring-red-200' : ''}`}
      />
      {erro && <p className="mt-1 text-xs font-semibold text-red-600">{erro}</p>}
      {!erro && dica && <p className="mt-1 text-xs text-slate-400">{dica}</p>}
    </label>
  );
}

export default Cadastro;
