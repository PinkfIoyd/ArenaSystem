import { useEffect, useState } from 'react';

function useDebounce(valor, delay = 300) {
  const [valorDebouncado, setValorDebouncado] = useState(valor);

  useEffect(() => {
    const timer = setTimeout(() => {
      setValorDebouncado(valor);
    }, delay);

    return () => clearTimeout(timer);
  }, [valor, delay]);

  return valorDebouncado;
}

export default useDebounce;
