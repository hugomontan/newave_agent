"use client";

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";
import { Download, Search } from "lucide-react";

interface DataTableProps {
  data: Record<string, unknown>[];
  title?: string;
}

export function DataTable({ data, title }: DataTableProps) {
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");

  const columns = useMemo(() => {
    if (data.length === 0) return [];
    return Object.keys(data[0]);
  }, [data]);

  const filteredData = useMemo(() => {
    if (!searchTerm) return data;
    return data.filter((row) =>
      Object.values(row).some((value) =>
        String(value).toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [data, searchTerm]);

  const paginatedData = useMemo(() => {
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    return filteredData.slice(start, end);
  }, [filteredData, page, rowsPerPage]);

  const totalPages = Math.ceil(filteredData.length / rowsPerPage);

  const downloadAsCSV = () => {
    const headers = columns.join(",");
    const rows = data.map((row) =>
      columns.map((col) => {
        const value = row[col];
        const stringValue = String(value ?? "");
        if (stringValue.includes(",") || stringValue.includes('"')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(",")
    );
    const csv = [headers, ...rows].join("\n");
    
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `data_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (data.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-full overflow-visible"
    >
      <div className="bg-card border border-border shadow-sm rounded-lg overflow-hidden">
        <div className="pb-3 px-4 sm:px-6 pt-4 sm:pt-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
              {title && (
                <h3 className="text-lg font-semibold mb-0 text-card-foreground">
                  {title}
                </h3>
              )}
              <p className="text-sm text-muted-foreground mt-1">
                {filteredData.length} {filteredData.length === 1 ? "registro" : "registros"}
                {searchTerm && ` (filtrado de ${data.length})`}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setPage(1);
                  }}
                  className="pl-8 w-48 h-9"
                />
              </div>
              <Button 
                variant="outline" 
                size="sm" 
                className="h-9"
                onClick={downloadAsCSV}
              >
                <Download className="w-4 h-4 mr-1" />
                Baixar CSV
              </Button>
            </div>
          </div>
        </div>
        <div className="px-4 sm:px-6 pb-4 sm:pb-6 pt-0">
          <div className="overflow-x-auto -mx-4 sm:-mx-6 md:-mx-8 px-4 sm:px-6 md:px-8">
            <div className="inline-block min-w-full align-middle">
              <table className="w-full border-collapse table-auto">
                <thead>
                  <tr className="border-b border-border">
                    {columns.map((col) => (
                      <th
                        key={col}
                        className="px-3 sm:px-4 py-2.5 text-left text-xs font-medium text-card-foreground uppercase tracking-wider bg-background"
                        style={{ 
                          minWidth: '120px',
                          maxWidth: '250px',
                          wordBreak: 'break-word',
                          overflowWrap: 'break-word'
                        }}
                        title={col}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {paginatedData.map((row, rowIndex) => (
                    <tr
                      key={rowIndex}
                      className="border-b border-border hover:bg-background transition-colors"
                    >
                      {columns.map((col) => {
                        const cellValue = String(row[col] ?? "");
                        return (
                          <td
                            key={col}
                            className="px-3 sm:px-4 py-2.5 text-xs sm:text-sm text-card-foreground/90"
                            style={{ 
                              minWidth: '120px',
                              maxWidth: '250px',
                              wordBreak: 'break-word',
                              overflowWrap: 'break-word'
                            }}
                            title={cellValue.length > 50 ? cellValue : undefined}
                          >
                            {cellValue}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mt-4 pt-4 border-t border-border px-4 sm:px-0">
              <div className="flex items-center gap-2">
                <span className="text-xs sm:text-sm text-muted-foreground">Linhas por página:</span>
                <select
                  value={rowsPerPage}
                  onChange={(e) => {
                    setRowsPerPage(Number(e.target.value));
                    setPage(1);
                  }}
                  className="text-xs sm:text-sm border border-border rounded px-2 py-1 text-foreground bg-background"
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="h-8 text-xs sm:text-sm"
                >
                  Anterior
                </Button>
                <span className="text-xs sm:text-sm text-muted-foreground">
                  Página {page} de {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="h-8 text-xs sm:text-sm"
                >
                  Próxima
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
