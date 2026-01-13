/**
 * Função utilitária para exportar dados de tabela para CSV
 */

export interface CSVExportData {
  [key: string]: string | number | null | undefined;
}

/**
 * Exporta dados para CSV
 * @param data Array de objetos com os dados da tabela
 * @param filename Nome do arquivo (sem extensão)
 * @param headers Mapeamento opcional de chaves para nomes de colunas (ex: { "deck_1": "Deck 1" })
 */
export function exportToCSV(
  data: CSVExportData[],
  filename: string = "tabela",
  headers?: Record<string, string>
): void {
  if (!data || data.length === 0) {
    return;
  }

  // Obter todas as chaves únicas dos dados
  const allKeys = new Set<string>();
  data.forEach((row) => {
    Object.keys(row).forEach((key) => allKeys.add(key));
  });

  const columns = Array.from(allKeys);

  // Criar cabeçalhos usando o mapeamento ou as chaves originais
  const csvHeaders = columns.map((col) => {
    if (headers && headers[col]) {
      return headers[col];
    }
    // Converter snake_case para título legível
    return col
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  });

  // Criar linhas CSV
  const rows = data.map((row) =>
    columns.map((col) => {
      const value = row[col];
      const stringValue = String(value ?? "");
      // Escapar valores que contêm vírgula ou aspas
      if (stringValue.includes(",") || stringValue.includes('"') || stringValue.includes("\n")) {
        return `"${stringValue.replace(/"/g, '""')}"`;
      }
      return stringValue;
    })
  );

  // Combinar cabeçalhos e linhas
  const csv = [csvHeaders.join(","), ...rows.map((row) => row.join(","))].join("\n");

  // Criar blob e fazer download
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
