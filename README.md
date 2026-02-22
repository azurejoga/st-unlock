# SteamUnlocked API

Uma API REST em Python com interface web para pesquisar e obter links de download do site SteamUnlocked.

## Funcionalidades

- **Interface Web** completa com busca e navegação
- **Pesquisar jogos** por nome
- **Obter detalhes** de jogos (descrição, requisitos de sistema, screenshots)
- **Extrair links de download** (UploadHaven, MegaUp, etc.)
- **Auto-download** com Playwright (clique automático no botão de download)
- **Navegar por categorias** (Action, RPG, Horror, etc.)
- **Listar jogos de A-Z**

## Instalação Rápida (Windows)

### Script de Instalação Automática

Para usuários Windows, use o script PowerShell automatizado:

```powershell
.\install.ps1
```

Este script irá:
1. Instalar Python 3.11 em modo silencioso (se não estiver instalado)
2. Criar ambiente virtual e instalar dependências
3. Instalar navegadores Playwright (Chromium)
4. Iniciar o servidor em segundo plano
5. Abrir o navegador em `http://127.0.0.1:5000`

### Instalação Manual

#### Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)

#### Passos

1. Clone ou baixe este projeto

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Instale o navegador Playwright:
```bash
playwright install chromium
```

4. (Opcional) Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

Edite o arquivo `.env` conforme necessário:
```
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
HEADLESS_BROWSER=false
REQUEST_DELAY=1.0
```

## Uso

### Iniciar a Aplicação Web

```bash
python web_app.py
```

A aplicação estará disponível em:
- Interface Web: `http://localhost:5000`
- API REST: `http://localhost:5000/api/*`

### Interface Web

Acesse `http://localhost:5000` no navegador para:
- Pesquisar jogos
- Navegar por categorias
- Ver lista de jogos A-Z
- Visualizar detalhes dos jogos
- Iniciar download automático com Playwright

### Endpoints da API

#### 1. Pesquisar Jogos

```bash
GET /api/search?q=<query>&limit=<n>
```

Exemplo:
```bash
curl "http://localhost:5000/api/search?q=diablo&limit=10"
```

#### 2. Obter Detalhes do Jogo

```bash
GET /api/game-info?slug=<slug>
```

Exemplo:
```bash
curl "http://localhost:5000/api/game-info?slug=diablo-hellfire-free-download"
```

#### 3. Listar Categorias

```bash
GET /api/categories
```

#### 4. Jogos por Categoria

```bash
GET /api/category/<category>?page=<n>
```

Exemplo:
```bash
curl "http://localhost:5000/api/category/action?page=1"
```

Categorias disponíveis:
- ACTION, ADVENTURE, ANIME, CLASSICS, FPS, HORROR, INDIE
- OPEN WORLD, POPULAR, PS2, RACING, REMASTERED, RPG
- SIMULATION, SMALL GAMES, SPORTS, VIRTUAL REALITY

#### 5. Jogos de A-Z

```bash
GET /api/games/az?letter=<a-z>&page=<n>
```

Exemplo:
```bash
curl "http://localhost:5000/api/games/az?letter=a&page=1"
```

#### 6. Auto-Download com Playwright

```bash
POST /api/auto-download-playwright
Content-Type: application/json

{
  "url": "https://steamunlocked.org/<game-slug>",
  "headless": false
}
```

Exemplo com curl:
```bash
curl -X POST "http://localhost:5000/api/auto-download-playwright" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://steamunlocked.org/diablo-hellfire-free-download", "headless": false}'
```

Este endpoint:
1. Abre o navegador Chromium
2. Navega até a página do jogo no SteamUnlocked
3. Clica automaticamente no botão de download
4. Aguarda o countdown do UploadHaven
5. Inicia o download automaticamente

## Estrutura do Projeto

```
steamunlocked-api/
├── web_app.py            # Flask web application + API
├── scraper.py            # Lógica de scraping
├── models.py             # Modelos de dados
├── requirements.txt      # Dependências Python
├── .env.example         # Variáveis de ambiente (exemplo)
├── install.ps1          # Script de instalação Windows
├── templates/           # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── search.html
│   ├── category.html
│   ├── games_az.html
│   └── game.html
└── README.md            # Esta documentação
```

## Tecnologias Utilizadas

- **Flask** - Framework web para API REST e interface web
- **Playwright** - Automação de navegador para auto-download
- **BeautifulSoup4** - Parsing HTML
- **Requests** - Requisições HTTP

## Notas Importantes

### Rate Limiting
O scraper inclui um delay entre requisições (configurável via `REQUEST_DELAY`) para evitar bloqueios.

### Playwright Auto-Download
- Usa Chromium headless ou visível (configurável)
- Aguarda o countdown de 16 segundos do UploadHaven
- Clica automaticamente nos botões de download
- Funciona completamente em segundo plano

### Anti-Detection
O scraper:
- Usa headers realistas
- User-Agent configurável
- Delay entre requisições

## Solução de Problemas

### Erro: Playwright não encontrado
Execute:
```bash
playwright install chromium
```

### Erro de timeout
Aumente o valor de `PLAYWRIGHT_TIMEOUT` no arquivo `.env`.

### Bloqueio do site
Aumente o valor de `REQUEST_DELAY` para reduzir a frequência de requisições.

### Porta 5000 em uso
Altere `FLASK_PORT` no arquivo `.env`.

## Exemplos de Uso

### Python

```python
import requests

# Pesquisar jogos
response = requests.get("http://localhost:5000/api/search", params={"q": "gta", "limit": 5})
games = response.json()

# Obter detalhes
slug = games["results"][0]["slug"]
details = requests.get(f"http://localhost:5000/api/game-info", params={"slug": slug}).json()

# Iniciar auto-download
requests.post(
    "http://localhost:5000/api/auto-download-playwright",
    json={"url": details["url"], "headless": False}
)
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

// Pesquisar jogos
const search = await axios.get('http://localhost:5000/api/search', {
  params: { q: 'gta', limit: 5 }
});

// Obter detalhes
const details = await axios.get('http://localhost:5000/api/game-info', {
  params: { slug: search.data.results[0].slug }
});

// Iniciar auto-download
await axios.post('http://localhost:5000/api/auto-download-playwright', {
  url: details.data.url,
  headless: false
});
```

## Aviso Legal

Esta ferramenta foi criada para fins educacionais. Respeite os termos de serviço do Steam e use por sua conta e risco. Não distribuimos conteúdo pirata o ilegal neste repositório.

## Licença

Este projeto é open source e está disponível sob a licença MIT.
