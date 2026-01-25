# Script para matar todos os processos na porta 8000
Write-Host "Procurando processos na porta 8000..."

# Obter todos os PIDs únicos na porta 8000
$pids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($pids) {
    Write-Host "Encontrados processos: $($pids -join ', ')"
    foreach ($processId in $pids) {
        try {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Matando processo PID $processId ($($process.ProcessName))..."
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 500
            }
        } catch {
            Write-Host "Erro ao matar processo $processId : $($_.Exception.Message)"
        }
    }
} else {
    Write-Host "Nenhum processo encontrado na porta 8000"
}

# Aguardar um pouco e verificar novamente
Start-Sleep -Seconds 2
Write-Host "`nVerificando processos restantes na porta 8000..."
$remaining = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($remaining) {
    Write-Host "⚠️ Ainda há processos na porta 8000: $($remaining -join ', ')"
    Write-Host "Tentando matar processos Python relacionados..."
    Get-Process python* -ErrorAction SilentlyContinue | Where-Object { $_.Id -in $remaining } | 
        ForEach-Object { 
            Write-Host "Matando processo Python PID $($_.Id)..."
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue 
        }
} else {
    Write-Host "✅ Porta 8000 está livre!"
}
