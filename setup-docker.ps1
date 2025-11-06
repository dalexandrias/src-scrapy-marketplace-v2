# Script de Setup Docker - Scraper Marketplace
# Execute: .\setup-docker.ps1

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  SETUP DOCKER - SCRAPER MARKETPLACE" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar se Docker está instalado
Write-Host "[1/6] Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✅ Docker encontrado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker não encontrado! Instale Docker Desktop primeiro." -ForegroundColor Red
    Write-Host "  📥 Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# 2. Verificar Docker Compose
Write-Host "[2/6] Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "  ✅ Docker Compose encontrado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker Compose não encontrado!" -ForegroundColor Red
    exit 1
}

# 3. Criar arquivo .env se não existir
Write-Host "[3/6] Verificando arquivo .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ⚠️  Arquivo .env já existe. Deseja sobrescrever? (s/N)" -ForegroundColor Yellow
    $resposta = Read-Host
    if ($resposta -eq "s" -or $resposta -eq "S") {
        Copy-Item .env.example .env -Force
        Write-Host "  ✅ Arquivo .env sobrescrito" -ForegroundColor Green
    } else {
        Write-Host "  ℹ️  Mantendo .env existente" -ForegroundColor Cyan
    }
} else {
    Copy-Item .env.example .env
    Write-Host "  ✅ Arquivo .env criado a partir de .env.example" -ForegroundColor Green
    Write-Host "  ⚠️  IMPORTANTE: Edite .env e configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID" -ForegroundColor Yellow
}

# 4. Criar diretórios necessários
Write-Host "[4/6] Criando diretórios..." -ForegroundColor Yellow
$diretorios = @("data", "logs", "backups")
foreach ($dir in $diretorios) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "  ✅ Criado: $dir/" -ForegroundColor Green
    } else {
        Write-Host "  ℹ️  Já existe: $dir/" -ForegroundColor Cyan
    }
}

# 5. Verificar arquivo .env configurado
Write-Host "[5/6] Verificando configuração .env..." -ForegroundColor Yellow
$envContent = Get-Content .env -Raw

if ($envContent -match "TELEGRAM_BOT_TOKEN=seu_token_aqui" -or $envContent -match "TELEGRAM_BOT_TOKEN=$") {
    Write-Host "  ⚠️  TELEGRAM_BOT_TOKEN não configurado!" -ForegroundColor Red
    Write-Host "  📝 Edite o arquivo .env e configure:" -ForegroundColor Yellow
    Write-Host "     - TELEGRAM_BOT_TOKEN (obter via @BotFather)" -ForegroundColor Yellow
    Write-Host "     - TELEGRAM_CHAT_ID (obter via @userinfobot)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Deseja continuar mesmo assim? (s/N)" -ForegroundColor Yellow
    $continuar = Read-Host
    if ($continuar -ne "s" -and $continuar -ne "S") {
        Write-Host "  ❌ Setup cancelado. Configure .env e execute novamente." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✅ Arquivo .env configurado" -ForegroundColor Green
}

# 6. Perguntar se deseja fazer build
Write-Host "[6/6] Docker Build..." -ForegroundColor Yellow
Write-Host "  Deseja fazer build da imagem agora? (S/n)" -ForegroundColor Yellow
$build = Read-Host
if ($build -eq "" -or $build -eq "s" -or $build -eq "S") {
    Write-Host ""
    Write-Host "  🔨 Executando docker-compose build..." -ForegroundColor Cyan
    Write-Host "  ⏳ Isso pode levar alguns minutos..." -ForegroundColor Yellow
    Write-Host ""
    docker-compose build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  ✅ Build concluído com sucesso!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "  ❌ Erro no build. Verifique os logs acima." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ℹ️  Build pulado. Execute manualmente: docker-compose build" -ForegroundColor Cyan
}

# Resumo final
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  ✅ SETUP CONCLUÍDO!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Edite .env e configure:" -ForegroundColor White
Write-Host "     - TELEGRAM_BOT_TOKEN" -ForegroundColor Gray
Write-Host "     - TELEGRAM_CHAT_ID" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Inicie o container:" -ForegroundColor White
Write-Host "     docker-compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Veja os logs:" -ForegroundColor White
Write-Host "     docker-compose logs -f" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Verifique status:" -ForegroundColor White
Write-Host "     docker-compose ps" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Documentação completa: docs/DOCKER.md" -ForegroundColor Yellow
Write-Host ""
