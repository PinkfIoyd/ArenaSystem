import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import api from '../../api/client';
import { adminNavigationFor } from '../../auth/permissions';
import Icon from '../Icon';
import { useArenaContext } from '../../contexts/arenaContextStore';
import useTerminology from '../../hooks/useTerminology';

function MenuMobileAdmin() {
  const [usuario, setUsuario] = useState(null);
  const { contexto } = useArenaContext();
  const { terms, features } = useTerminology();

  useEffect(() => {
    let active = true;
    async function carregarUsuario() {
      try {
        const { data } = await api.get('/usuarios/me/');
        if (active) setUsuario(data);
      } catch {
        if (active) setUsuario(null);
      }
    }
    void carregarUsuario();
    return () => {
      active = false;
    };
  }, []);

  const itens = adminNavigationFor(usuario, { terms, features, hasTenantContext: Boolean(contexto) });

  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-slate-900 bg-slate-950 px-2 py-2 text-white md:hidden">
      {itens.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          end={item.exact}
          className={({ isActive }) =>
            `flex min-w-[86px] flex-col items-center justify-center rounded-md px-2 py-1.5 text-xs transition ${
              isActive ? 'admin-mobile-nav-active font-bold' : 'text-slate-400'
            }`
          }
        >
          <Icon name={item.icon} className="h-5 w-5" />
          <span className="text-[10px] mt-0.5 whitespace-nowrap">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default MenuMobileAdmin;
