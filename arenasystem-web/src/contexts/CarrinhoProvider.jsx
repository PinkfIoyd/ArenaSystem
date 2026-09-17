import { useEffect, useState } from 'react';

import { CarrinhoContext } from './CarrinhoStore';

export function CarrinhoProvider({ children }) {
  const [itens, setItens] = useState(() => {
    try {
      const salvo = localStorage.getItem('carrinho');
      const itensSalvos = salvo ? JSON.parse(salvo) : [];
      return Array.isArray(itensSalvos) ? itensSalvos : [];
    } catch {
      localStorage.removeItem('carrinho');
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem('carrinho', JSON.stringify(itens));
  }, [itens]);

  const adicionar = (produto) => {
    setItens((atual) => {
      const existente = atual.find((i) => i.produto.id === produto.id);
      if (existente) {
        return atual.map((i) =>
          i.produto.id === produto.id
            ? { ...i, quantidade: i.quantidade + 1 }
            : i,
        );
      }
      return [...atual, { produto, quantidade: 1 }];
    });
  };

  const remover = (produtoId) => {
    setItens((atual) => atual.filter((i) => i.produto.id !== produtoId));
  };

  const alterarQuantidade = (produtoId, quantidade) => {
    if (quantidade <= 0) {
      remover(produtoId);
      return;
    }
    setItens((atual) =>
      atual.map((i) =>
        i.produto.id === produtoId ? { ...i, quantidade } : i,
      ),
    );
  };

  const limpar = () => setItens([]);

  const totalItens = itens.reduce((acc, i) => acc + i.quantidade, 0);
  const totalValor = itens.reduce(
    (acc, i) => acc + Number(i.produto.preco) * i.quantidade,
    0,
  );

  const valor = {
    itens,
    adicionar,
    remover,
    alterarQuantidade,
    limpar,
    totalItens,
    totalValor,
  };

  return (
    <CarrinhoContext.Provider value={valor}>
      {children}
    </CarrinhoContext.Provider>
  );
}
