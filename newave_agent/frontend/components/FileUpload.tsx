"use client";

import React, { useState, useRef, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { uploadDeck, UploadResponse } from "@/lib/api";
import { Upload, File, Loader2 } from "lucide-react";

interface FileUploadProps {
  onUploadSuccess: (response: UploadResponse) => void;
  disabled?: boolean;
}

export function FileUpload({ onUploadSuccess, disabled }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await handleFile(files[0]);
    }
  }, []);

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        await handleFile(files[0]);
      }
    },
    []
  );

  const handleFile = async (file: File) => {
    if (!file.name.endsWith(".zip")) {
      setError("Por favor, selecione um arquivo .zip");
      return;
    }

    setError(null);
    setIsUploading(true);
    setUploadProgress(0);

    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + 10;
      });
    }, 200);

    try {
      const response = await uploadDeck(file);
      setUploadProgress(100);
      clearInterval(progressInterval);
      
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
        onUploadSuccess(response);
      }, 500);
    } catch (err) {
      clearInterval(progressInterval);
      setIsUploading(false);
      setUploadProgress(0);
      setError(err instanceof Error ? err.message : "Erro ao fazer upload");
    }
  };

  return (
    <Card
      className={`border-2 border-dashed transition-all duration-200 ${
        isDragging
          ? "border-primary/50 bg-background shadow-sm"
          : "border-border hover:border-primary/50 bg-background hover:shadow-sm"
      } ${disabled ? "opacity-50 pointer-events-none" : ""} rounded-xl`}
    >
      <CardContent
        className="flex flex-col items-center justify-center py-10 cursor-pointer"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip"
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled || isUploading}
        />

        {isUploading ? (
          <div className="w-full max-w-xs space-y-4">
            <div className="flex items-center justify-center">
              <Loader2 className="h-10 w-10 animate-spin text-primary" />
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-center text-sm text-muted-foreground">
              Enviando arquivo... {uploadProgress}%
            </p>
          </div>
        ) : (
          <>
            <div className="w-16 h-16 mb-4 rounded-full bg-card flex items-center justify-center border-2 border-border">
              <Upload className="w-8 h-8 text-muted-foreground" />
            </div>
            <p className="text-lg font-medium mb-2 text-foreground">
              Arraste seu deck NEWAVE aqui
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              ou clique para selecionar
            </p>
            <Badge variant="outline">
              <File className="w-3 h-3 mr-1" />
              Apenas arquivos .zip
            </Badge>
          </>
        )}

        {error && (
          <div className="mt-4 p-3 bg-destructive/20 border border-destructive rounded-lg max-w-md">
            <p className="text-destructive-foreground text-sm">{error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
