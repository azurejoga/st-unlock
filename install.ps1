# SteamUnlocked API - Script de Instalacao Automatica
# Este script instala Python 3.11, dependencias, Playwright e inicia o servidor

# Configuracao de codificacao para exibir corretamente caracteres especiais
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Funcao para imprimir mensagens com cores
function Write-ColorOutput {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,

        [Parameter(Mandatory=$false)]
        [string]$Color = "White"
    )

    Write-Host $Message -ForegroundColor $Color
}

# Funcao para verificar se o comando existe
function Test-CommandExists {
    param([string]$Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $Command) { return $true }
    }
    catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
}

# Funcao para verificar se Python 3.11 esta instalado
function Get-Python311 {
    $pythonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python3.11-32\python.exe",
        "$env:APPDATA\Python\Python311\python.exe",
        "C:\Python311\python.exe",
        "C:\Program Files\Python311\python.exe"
    )

    foreach ($path in $pythonPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    # Tenta encontrar via comando
    try {
        $version = & python --version 2>&1
        if ($version -match "3\.11\.\d+") {
            return "python"
        }
    } catch {}

    return $null
}

# Banner inicial
Clear-Host
Write-ColorOutput "========================================================" "Cyan"
Write-ColorOutput "     SteamUnlocked API - Script de Instalacao Automatica" "Cyan"
Write-ColorOutput "========================================================" "Cyan"
Write-Host ""

# Passo 1: Verificar/Instalar Python 3.11
Write-ColorOutput "[1/5] Verificando Python 3.11..." "Yellow"

$pythonPath = Get-Python311

if ($null -eq $pythonPath) {
    Write-ColorOutput "   Python 3.11 nao encontrado. Iniciando instalacao..." "Red"

    # Cria diretorio temporario para download
    $tempDir = Join-Path $env:TEMP "python311_install"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    # URL do Python 3.11 (versao mais recente)
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $pythonInstaller = Join-Path $tempDir "python311_installer.exe"

    Write-ColorOutput "   Baixando Python 3.11.9..." "Gray"

    try {
        # Verifica se tem bitsadmin para download (mais confiavel)
        $downloadSuccess = $false

        # Tenta com Invoke-WebRequest primeiro
        try {
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
            $downloadSuccess = $true
        } catch {
            # Fallback para bitsadmin
            Write-ColorOutput "   Tentando metodo alternativo de download..." "Gray"
            $process = Start-Process -FilePath "bitsadmin.exe" -ArgumentList "/transfer pythonDownload /download /priority normal $pythonUrl $pythonInstaller" -NoNewWindow -PassThru -Wait
            if ($process.ExitCode -eq 0) {
                $downloadSuccess = $true
            }
        }

        if ($downloadSuccess -and (Test-Path $pythonInstaller)) {
            Write-ColorOutput "   Instalando Python 3.11 (modo silencioso)..." "Gray"

            # Instala Python 3.11 com todas as opcoes necessarias
            $installArgs = @(
                "/quiet",
                "InstallAllUsers=0",
                "PrependPath=1",
                "Include_test=0",
                "Include_pip=1",
                "Include_lib=1"
            )

            $process = Start-Process -FilePath $pythonInstaller -ArgumentList $installArgs -Wait -PassThru

            if ($process.ExitCode -eq 0) {
                Write-ColorOutput "   Python 3.11 instalado com sucesso!" "Green"

                # Atualiza PATH para sessao atual
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")

                # Aguarda um momento para a instalacao completar
                Start-Sleep -Seconds 3

                # Busca novamente o Python
                $pythonPath = Get-Python311
                if ($null -eq $pythonPath) {
                    # Tenta usar python direto
                    $pythonPath = "python"
                }
            } else {
                Write-ColorOutput "   ERRO: Falha na instalacao do Python!" "Red"
                Write-ColorOutput "   Codigo de saida: $($process.ExitCode)" "Red"
                Write-ColorOutput "   Por favor, instale Python 3.11 manualmente de: https://www.python.org/downloads/" "Yellow"
                pause
                exit 1
            }
        } else {
            Write-ColorOutput "   ERRO: Falha no download do Python!" "Red"
            Write-ColorOutput "   Por favor, instale Python 3.11 manualmente de: https://www.python.org/downloads/" "Yellow"
            pause
            exit 1
        }

    } catch {
        Write-ColorOutput "   ERRO: $($_.Exception.Message)" "Red"
        Write-ColorOutput "   Por favor, instale Python 3.11 manualmente de: https://www.python.org/downloads/" "Yellow"
        pause
        exit 1
    }
    finally {
        # Limpa arquivos temporarios
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-ColorOutput "   Python 3.11 encontrado: $pythonPath" "Green"
}

# Passo 2: Instalar dependencias Python
Write-Host ""
Write-ColorOutput "[2/5] Instalando dependencias Python..." "Yellow"

if (Test-Path "requirements.txt") {
    Write-ColorOutput "   Instalando pacotes do requirements.txt..." "Gray"

    try {
        # Usa o Python encontrado ou o padrao
        $pipCmd = & $pythonPath -m pip --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "   pip encontrado!" "Green"

            # Atualiza pip
            & $pythonPath -m pip install --upgrade pip --quiet

            # Instala dependencias
            & $pythonPath -m pip install -r requirements.txt --quiet

            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "   Dependencias instaladas com sucesso!" "Green"
            } else {
                Write-ColorOutput "   Aviso: Alguns pacotes podem nao ter sido instalados corretamente." "Yellow"
            }
        } else {
            Write-ColorOutput "   ERRO: pip nao encontrado!" "Red"
            pause
            exit 1
        }
    } catch {
        Write-ColorOutput "   ERRO ao instalar dependencias: $($_.Exception.Message)" "Red"
        pause
        exit 1
    }
} else {
    Write-ColorOutput "   ERRO: Arquivo requirements.txt nao encontrado!" "Red"
    pause
    exit 1
}

# Passo 3: Instalar navegador Playwright
Write-Host ""
Write-ColorOutput "[3/5] Instalando navegador Playwright (Chromium)..." "Yellow"

try {
    # Verifica se playwright install esta disponivel
    $playwrightCheck = & $pythonPath -m playwright --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "   Playwright encontrado: $playwrightCheck" "Green"
        Write-ColorOutput "   Baixando Chromium (pode levar alguns minutos)..." "Gray"

        # Instala apenas Chromium
        & $pythonPath -m playwright install chromium

        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "   Chromium instalado com sucesso!" "Green"
        } else {
            Write-ColorOutput "   Aviso: A instalacao do Chromium pode ter falhado." "Yellow"
            Write-ColorOutput "   Execute manualmente: python -m playwright install chromium" "Yellow"
        }
    } else {
        Write-ColorOutput "   Aviso: Playwright nao encontrado. Pulando instalacao do navegador." "Yellow"
    }
} catch {
    Write-ColorOutput "   Erro na instalacao do Playwright: $($_.Exception.Message)" "Yellow"
    Write-ColorOutput "   Execute manualmente: python -m playwright install chromium" "Yellow"
}

# Passo 4: Verificar/Instalar python-dotenv para carregar variaveis de ambiente
Write-Host ""
Write-ColorOutput "[4/5] Configurando ambiente..." "Yellow"

# Cria arquivo .env se nao existir
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-ColorOutput "   Criando arquivo .env a partir de .env.example..." "Gray"
        Copy-Item ".env.example" ".env"
        Write-ColorOutput "   Arquivo .env criado!" "Green"
    } else {
        Write-ColorOutput "   Arquivo .env.example nao encontrado. Criando .env padrao..." "Gray"
        $envContent = @"
FLASK_ENV=development
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
HEADLESS_BROWSER=false
PLAYWRIGHT_TIMEOUT=30000
REQUEST_DELAY=1.0
DOWNLOAD_TIMEOUT=120
USER_AGENT_ROTATION=true
MAX_RETRIES=3
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-ColorOutput "   Arquivo .env criado!" "Green"
    }
} else {
    Write-ColorOutput "   Arquivo .env ja existe!" "Green"
}

# Passo 5: Iniciar servidor em segundo plano
Write-Host ""
Write-ColorOutput "[5/5] Iniciando servidor Flask em segundo plano..." "Yellow"

# Cria script de inicializacao
$startScript = @"
# Script de inicializacao do servidor SteamUnlocked API
# Gerado automaticamente pelo install.ps1

`$scriptDir = Split-Path -Parent `$MyInvocation.MyCommand.Path
cd `$scriptDir

Write-Host "Iniciando SteamUnlocked API..." -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar o servidor." -ForegroundColor Yellow
Write-Host ""

# Executa o aplicativo Flask
python web_app.py
"@

$startScriptPath = "start_server.ps1"
$startScript | Out-File -FilePath $startScriptPath -Encoding UTF8

Write-ColorOutput "   Script de inicializacao criado: $startScriptPath" "Green"

# Inicia o servidor em uma nova janela sem bloquear
Write-ColorOutput "   Iniciando servidor em nova janela..." "Gray"

$serverProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$startScriptPath`"" -WindowStyle Minimized

Start-Sleep -Seconds 2

# Verifica se o processo esta rodando
if (Get-Process -Id $serverProcess.Id -ErrorAction SilentlyContinue) {
    Write-ColorOutput "   Servidor iniciado com sucesso!" "Green"
} else {
    Write-ColorOutput "   Aviso: Nao foi possivel verificar se o servidor iniciou." "Yellow"
}

# Mensagem final
Write-Host ""
Write-ColorOutput "========================================================" "Cyan"
Write-ColorOutput "                   Instalacao Concluida!" "Green"
Write-ColorOutput "========================================================" "Cyan"
Write-Host ""
Write-ColorOutput "A aplicacao esta rodando em:" "Yellow"
Write-Host "   http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""
Write-ColorOutput "Para usar:" "Yellow"
Write-Host "   1. Abra seu navegador e acesse: http://127.0.0.1:5000" -ForegroundColor White
Write-Host "   2. Pesquise por jogos, navegue por categorias ou veja A-Z" -ForegroundColor White
Write-Host "   3. Clique em um jogo para ver detalhes e iniciar o download" -ForegroundColor White
Write-Host ""
Write-ColorOutput "Comandos uteis:" "Yellow"
Write-Host "   - Parar o servidor: Feche a janela minimizada do PowerShell" -ForegroundColor White
Write-Host "   - Reiniciar o servidor: .\start_server.ps1" -ForegroundColor White
Write-Host "   - Ver logs: Observe a janela minimizada do PowerShell" -ForegroundColor White
Write-Host ""

# Tenta abrir o navegador automaticamente
Write-ColorOutput "Abrindo navegador..." "Gray"
Start-Process "http://127.0.0.1:5000" -ErrorAction SilentlyContinue

Write-ColorOutput "Pressione qualquer tecla para sair (o servidor continuara rodando)..." "Yellow"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-ColorOutput "O servidor continuara rodando em segundo plano." "Green"
Write-ColorOutput "Para para-lo, feche a janela minimizada do PowerShell." "Yellow"
