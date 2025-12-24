"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, Upload, RefreshCw, Trash2, Circle } from "lucide-react";

interface SessionPanelProps {
  sessionId: string | null;
  filesCount: number;
  files: string[];
  onClearSession: () => void;
  onReindex: () => void;
  isReindexing: boolean;
}

export function SessionPanel({
  sessionId,
  filesCount,
  files,
  onClearSession,
  onReindex,
  isReindexing,
}: SessionPanelProps) {
  return (
    <div className="h-full p-4">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-sm font-semibold text-btg-graphite-900 tracking-tight mb-3">
            Sessão Ativa
          </h2>
          {sessionId ? (
            <Badge variant="default" className="w-fit bg-green-50 text-green-700 border-green-200 text-xs font-medium">
              <Circle className="w-1.5 h-1.5 fill-green-600 mr-1.5" />
              Conectado
            </Badge>
          ) : (
            <Badge variant="secondary" className="w-fit bg-yellow-50 text-yellow-700 border-yellow-200 text-xs font-medium">
              <Circle className="w-1.5 h-1.5 fill-yellow-500 mr-1.5" />
              Aguardando
            </Badge>
          )}
        </div>

        <Separator />

        {sessionId ? (
          <>
            {/* Session ID */}
            <div>
              <p className="text-xs text-btg-graphite-600 mb-2 font-medium uppercase tracking-wide">
                Session ID
              </p>
              <code className="text-xs bg-btg-graphite-50 text-btg-graphite-700 px-3 py-2 rounded-md block overflow-hidden text-ellipsis border border-btg-graphite-200 font-mono">
                {sessionId}
              </code>
            </div>

            {/* Files */}
            <div>
              <p className="text-xs text-btg-graphite-600 mb-2.5 font-medium uppercase tracking-wide">
                Arquivos ({filesCount})
              </p>
              <ScrollArea className="max-h-48">
                <div className="space-y-1.5 pr-3">
                  {files.slice(0, 20).map((file, index) => (
                    <div
                      key={index}
                      className="text-xs bg-btg-graphite-50 px-3 py-2 rounded-md flex items-center gap-2 border border-btg-graphite-200/60 hover:border-btg-navy/40 hover:bg-btg-graphite-100/50 transition-colors"
                    >
                      <FileText className="w-3.5 h-3.5 text-btg-graphite-500 flex-shrink-0" strokeWidth={2} />
                      <span className="truncate text-btg-graphite-700 font-normal">{file}</span>
                    </div>
                  ))}
                  {files.length > 20 && (
                    <p className="text-xs text-btg-graphite-400 italic pl-3 mt-2">
                      +{files.length - 20} arquivos...
                    </p>
                  )}
                </div>
              </ScrollArea>
            </div>

            <Separator />

            {/* Clear Session */}
            <Button
              size="sm"
              variant="outline"
              className="w-full border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 hover:border-red-300 h-9 rounded-md font-medium transition-colors"
              onClick={onClearSession}
            >
              <Trash2 className="w-3.5 h-3.5 mr-2" strokeWidth={2} />
              Limpar Sessão
            </Button>
          </>
        ) : (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-btg-graphite-100 flex items-center justify-center border border-btg-graphite-200">
              <Upload className="w-8 h-8 text-btg-graphite-400" strokeWidth={1.5} />
            </div>
            <p className="text-sm text-btg-graphite-600 font-normal leading-relaxed">
              Faça upload de um deck NEWAVE para começar
            </p>
          </div>
        )}

        <Separator />

        {/* Maintenance */}
        <div>
          <p className="text-xs text-btg-graphite-600 mb-2.5 font-medium uppercase tracking-wide">
            Manutenção
          </p>
          <Button
            size="sm"
            variant="outline"
            className="w-full border-btg-graphite-300 text-btg-graphite-700 hover:bg-btg-graphite-50 hover:border-btg-graphite-400 h-9 rounded-md font-medium transition-colors"
            onClick={onReindex}
            disabled={isReindexing}
          >
            {isReindexing ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Reindexando...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Reindexar Documentação
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
