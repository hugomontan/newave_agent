// Funções de formatação compartilhadas

export function formatNumber(value: number): string {
  if (value === null || value === undefined) return "-";
  // Se for número inteiro, não mostrar decimais
  if (Number.isInteger(value)) {
    return value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }
  return value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatInteger(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  // Formatar como inteiro (sem decimais)
  return value.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

export function formatPercent(value: number): string {
  if (value === null || value === undefined) return "-";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatMonth(mes: number | string): string {
  const meses = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
  ];
  const mesNum = typeof mes === 'number' ? mes : parseInt(String(mes), 10);
  if (mesNum >= 1 && mesNum <= 12) {
    return meses[mesNum - 1];
  }
  return String(mes);
}
