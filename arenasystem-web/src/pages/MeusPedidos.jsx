import { useCallback, useEffect, useState } from 'react';
import api from '../api/client';
import Layout from '../components/Layout';
import Badge from '../components/Badge';
import { formatarMoeda, formatarData } from '../utils/format';

function MeusPedidos() {
  const [pedidos, setPedidos] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [expandido, setExpandido] = useState(null);

  const carregarPedidos = useCallback(async () => {
    setCarregando(true);
    try {
      const { data } = await api.get('/vendas/');
      setPedidos(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      console.error('Erro:', err);
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    const id = setTimeout(carregarPedidos, 0);
    return () => clearTimeout(id);
  }, [carregarPedidos]);

  return (
    <Layout>
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">📦 Meus Pedidos</h2>
        <p className="text-gray-600">Histórico de compras e aluguéis</p>
      </div>

      {carregando ? (
        <div className="text-center py-12 text-gray-500">
          <div className="text-4xl mb-2">⏳</div>
          Carregando pedidos...
        </div>
      ) : pedidos.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl">
          <div className="text-5xl mb-3">📦</div>
          <p className="text-gray-600 font-medium">Você ainda não fez nenhum pedido</p>
          <p className="text-gray-400 text-sm mt-1">
            Visite a loja para fazer sua primeira compra!
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {pedidos.map((pedido) => (
            <div key={pedido.id} className="bg-white rounded-xl shadow-sm overflow-hidden">
              {/* Cabeçalho clicável */}
              <button
                onClick={() => setExpandido(expandido === pedido.id ? null : pedido.id)}
                className="w-full p-5 flex items-center justify-between hover:bg-gray-50 transition"
              >
                <div className="text-left">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-bold text-gray-800">
                      Pedido #{pedido.id}
                    </span>
                    <Badge
                      status={pedido.status}
                      texto={pedido.status.charAt(0).toUpperCase() + pedido.status.slice(1)}
                    />
                  </div>
                  <p className="text-sm text-gray-500">
                    {formatarData(pedido.data?.slice(0, 10))} • {pedido.itens?.length || 0} item(ns)
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xl font-bold text-teal-700">
                    {formatarMoeda(pedido.total)}
                  </span>
                  <span className={`text-2xl text-gray-400 transition-transform ${
                    expandido === pedido.id ? 'rotate-180' : ''
                  }`}>
                    ⌄
                  </span>
                </div>
              </button>

              {/* Itens expandidos */}
              {expandido === pedido.id && pedido.itens?.length > 0 && (
                <div className="border-t bg-gray-50 p-4 space-y-2">
                  {pedido.itens.map((item) => (
                    <div
                      key={item.id}
                      className="flex justify-between items-center bg-white p-3 rounded-lg"
                    >
                      <div>
                        <p className="font-medium text-gray-800">
                          {item.produto_nome}
                        </p>
                        <p className="text-xs text-gray-500">
                          {item.quantidade}x {formatarMoeda(item.preco_unitario)}
                        </p>
                      </div>
                      <p className="font-bold text-gray-700">
                        {formatarMoeda(item.subtotal || item.preco_unitario * item.quantidade)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}

export default MeusPedidos;
