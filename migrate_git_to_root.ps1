# Script para mover o repositório git de newave_agent para a raiz
# Isso permitirá incluir tanto newave_agent quanto decomp_agent no mesmo repositório

Write-Host "=== Migração do Repositório Git ===" -ForegroundColor Cyan
Write-Host ""

# Verificar se estamos no diretório correto
if (-not (Test-Path "newave_agent\.git")) {
    Write-Host "❌ Erro: Repositório git não encontrado em newave_agent\.git" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Repositório git encontrado em newave_agent\.git" -ForegroundColor Green
Write-Host ""

# Verificar se já existe .git na raiz
if (Test-Path ".git") {
    Write-Host "⚠️  Aviso: Já existe um .git na raiz!" -ForegroundColor Yellow
    Write-Host "   Deseja continuar mesmo assim? (S/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne "S" -and $response -ne "s") {
        Write-Host "❌ Operação cancelada" -ForegroundColor Red
        exit 1
    }
}

Write-Host "📦 Passo 1: Fazendo backup do .git atual..." -ForegroundColor Cyan
Copy-Item -Path "newave_agent\.git" -Destination "newave_agent\.git.backup" -Recurse -Force
Write-Host "   ✅ Backup criado em newave_agent\.git.backup" -ForegroundColor Green

Write-Host ""
Write-Host "📦 Passo 2: Movendo .git para a raiz..." -ForegroundColor Cyan
Move-Item -Path "newave_agent\.git" -Destination ".git" -Force
Write-Host "   ✅ .git movido para a raiz" -ForegroundColor Green

Write-Host ""
Write-Host "📦 Passo 3: Atualizando .gitignore..." -ForegroundColor Cyan

# Criar/atualizar .gitignore na raiz
$gitignoreContent = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
.env
.ENV

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Projeto específico
data/
uploads/
*.log

# Frontend
node_modules/
.next/
dist/
build/

# Backup
*.backup
.git.backup/
"@

Set-Content -Path ".gitignore" -Value $gitignoreContent
Write-Host "   ✅ .gitignore criado/atualizado na raiz" -ForegroundColor Green

Write-Host ""
Write-Host "📦 Passo 4: Adicionando arquivos ao git..." -ForegroundColor Cyan

# Adicionar todos os arquivos (incluindo decomp_agent)
git add .
Write-Host "   ✅ Arquivos adicionados ao staging" -ForegroundColor Green

Write-Host ""
Write-Host "✅ Migração concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "  1. Verifique o status: git status" -ForegroundColor Yellow
Write-Host "  2. Revise as mudanças: git diff --cached" -ForegroundColor Yellow
Write-Host "  3. Faça commit se estiver tudo ok: git commit -m 'Migração: incluir decomp_agent no repositório'" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  Nota: O backup está em newave_agent\.git.backup caso precise reverter" -ForegroundColor Yellow
