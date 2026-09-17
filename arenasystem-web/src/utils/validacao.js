// Valida formato de email
export function validarEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// Valida CPF (formato e dígitos verificadores)
export function validarCPF(cpf) {
  cpf = cpf.replace(/\D/g, ''); // remove tudo que não é número

  if (cpf.length !== 11) return false;
  if (/^(\d)\1+$/.test(cpf)) return false; // CPFs como 11111111111 são inválidos

  let soma = 0;
  for (let i = 0; i < 9; i++) {
    soma += parseInt(cpf.charAt(i)) * (10 - i);
  }
  let resto = (soma * 10) % 11;
  if (resto === 10 || resto === 11) resto = 0;
  if (resto !== parseInt(cpf.charAt(9))) return false;

  soma = 0;
  for (let i = 0; i < 10; i++) {
    soma += parseInt(cpf.charAt(i)) * (11 - i);
  }
  resto = (soma * 10) % 11;
  if (resto === 10 || resto === 11) resto = 0;
  if (resto !== parseInt(cpf.charAt(10))) return false;

  return true;
}

// Formata CPF: 12345678900 → 123.456.789-00
export function formatarCPF(cpf) {
  cpf = cpf.replace(/\D/g, '').slice(0, 11);
  return cpf
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

// Formata telefone: 11999999999 → (11) 99999-9999
export function formatarTelefone(telefone) {
  telefone = telefone.replace(/\D/g, '').slice(0, 11);
  if (telefone.length <= 10) {
    return telefone
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2');
  }
  return telefone
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2');
}

// Avalia a força da senha (0 a 4)
export function forcaSenha(senha) {
  let pontos = 0;
  if (senha.length >= 8) pontos++;
  if (/[A-Z]/.test(senha)) pontos++;
  if (/[a-z]/.test(senha)) pontos++;
  if (/[0-9]/.test(senha)) pontos++;
  if (/[^A-Za-z0-9]/.test(senha)) pontos++;
  return Math.min(pontos, 4);
}