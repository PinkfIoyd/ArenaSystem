import { useContext } from 'react';

import { CarrinhoContext } from './CarrinhoStore';

export function useCarrinho() {
  return useContext(CarrinhoContext);
}
