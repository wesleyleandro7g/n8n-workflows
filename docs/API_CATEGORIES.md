# API de Categorias - Documentação

## 📋 Visão Geral

O projeto agora possui **dois endpoints** para buscar workflows por categoria, cada um com abordagem diferente:

### 1️⃣ Categorias por Integrações (Hardcoded)

**Endpoint:** `/api/workflows/category/{category}`

Busca workflows baseado nas **integrações/serviços** que eles utilizam.

### 2️⃣ Categorias do JSON (Pré-categorizados)

**Endpoint:** `/api/workflows/by-json-category/{category}`

Busca workflows usando categorias **pré-definidas** no arquivo `context/search_categories.json`.

---

## 🔥 Novo Endpoint: `/api/workflows/by-json-category/{category}`

### Descrição

Retorna workflows filtrados por categoria usando o mapeamento manual definido em `context/search_categories.json`.

### Categorias Disponíveis

```
- AI Agent Development
- Business Process Automation
- CRM & Sales
- Cloud Storage & File Management
- Communication & Messaging
- Creative Content & Video Automation
- Creative Design Automation
- Data Processing & Analysis
- E-commerce & Retail
- Financial & Accounting
- Marketing & Advertising Automation
- Project Management
- Social Media Management
- Technical Infrastructure & DevOps
- Uncategorized
- Web Scraping & Data Extraction
```

### Parâmetros

| Parâmetro  | Tipo            | Obrigatório | Descrição                | Padrão |
| ---------- | --------------- | ----------- | ------------------------ | ------ |
| `category` | string (path)   | ✅ Sim      | Nome exato da categoria  | -      |
| `page`     | integer (query) | ❌ Não      | Número da página         | 1      |
| `per_page` | integer (query) | ❌ Não      | Items por página (1-100) | 20     |

### Exemplos de Uso

#### 1. Buscar workflows de IA

```bash
curl "http://localhost:8000/api/workflows/by-json-category/AI%20Agent%20Development"
```

#### 2. Buscar workflows de comunicação (com paginação)

```bash
curl "http://localhost:8000/api/workflows/by-json-category/Communication%20%26%20Messaging?page=1&per_page=10"
```

#### 3. Buscar workflows de automação

```bash
curl "http://localhost:8000/api/workflows/by-json-category/Business%20Process%20Automation"
```

### Resposta de Sucesso (200 OK)

```json
{
  "workflows": [
    {
      "id": 123,
      "filename": "telegram_bot_automation.json",
      "name": "Telegram Bot Automation",
      "active": true,
      "description": "Automated Telegram bot with AI responses",
      "trigger_type": "Webhook",
      "complexity": "medium",
      "node_count": 8,
      "integrations": ["Telegram", "OpenAI"],
      "tags": ["automation", "ai", "messaging"],
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-03-20T14:45:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20,
  "pages": 3,
  "query": "json_category:Communication & Messaging",
  "filters": {
    "json_category": "Communication & Messaging"
  }
}
```

### Códigos de Erro

| Código | Descrição                                       | Solução                                     |
| ------ | ----------------------------------------------- | ------------------------------------------- |
| `404`  | Arquivo `search_categories.json` não encontrado | Verificar se o arquivo existe em `context/` |
| `500`  | Erro interno no servidor                        | Verificar logs do servidor                  |

---

## 🆚 Comparação: Qual Endpoint Usar?

### Use `/api/workflows/category/{category}` quando:

- ✅ Quiser buscar por **tipo de serviço/integração**
- ✅ Categorias baseadas em tecnologia (ex: `messaging`, `database`)
- ✅ Busca automática baseada nas integrações detectadas

**Exemplo:**

```bash
GET /api/workflows/category/messaging
# Retorna todos os workflows que usam Telegram, Discord, Slack, etc.
```

### Use `/api/workflows/by-json-category/{category}` quando:

- ✅ Quiser buscar por **caso de uso/propósito**
- ✅ Categorias baseadas em função (ex: "AI Agent Development", "Business Process Automation")
- ✅ Precisar de categorização **manual e precisa**

**Exemplo:**

```bash
GET /api/workflows/by-json-category/AI%20Agent%20Development
# Retorna apenas workflows manualmente categorizados como IA
```

---

## 📊 Diagrama de Funcionamento

```
┌─────────────────┐
│  Cliente/UI     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  GET /api/workflows/by-json-category/{category}     │
│  Ex: "Communication & Messaging"                    │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  1. Carrega context/search_categories.json          │
│  2. Filtra filenames por category                   │
│  3. Busca workflows no SQLite (WHERE filename IN)   │
│  4. Retorna resultados paginados                    │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementação Técnica

### Fonte de Dados

O endpoint lê o arquivo `context/search_categories.json` que tem o formato:

```json
[
  {
    "filename": "telegram_bot.json",
    "category": "Communication & Messaging"
  },
  {
    "filename": "data_processor.json",
    "category": "Data Processing & Analysis"
  }
]
```

### Query SQL Gerada

Para categoria "AI Agent Development" com 3 workflows:

```sql
SELECT * FROM workflows
WHERE filename IN (?, ?, ?)
ORDER BY analyzed_at DESC
LIMIT 20 OFFSET 0
```

**Vantagens:**

- ✅ Performance superior (SQL IN é mais rápido que LIKE)
- ✅ Resultados exatos (sem falsos positivos)
- ✅ Fácil manutenção (apenas editar JSON)

---

## 🚀 Como Testar

### 1. Listar todas as categorias disponíveis

```bash
curl http://localhost:8000/api/categories
```

### 2. Buscar workflows de uma categoria

```bash
# Substitua espaços por %20 e & por %26
curl "http://localhost:8000/api/workflows/by-json-category/Communication%20%26%20Messaging"
```

### 3. Com JavaScript/Fetch

```javascript
const category = 'Communication & Messaging'
const encodedCategory = encodeURIComponent(category)

fetch(
  `http://localhost:8000/api/workflows/by-json-category/${encodedCategory}?page=1&per_page=10`
)
  .then((response) => response.json())
  .then((data) => {
    console.log(`Total workflows: ${data.total}`)
    console.log(`Workflows:`, data.workflows)
  })
```

### 4. Com Python

```python
import requests

category = "AI Agent Development"
response = requests.get(
    f"http://localhost:8000/api/workflows/by-json-category/{category}",
    params={"page": 1, "per_page": 20}
)

data = response.json()
print(f"Total: {data['total']}")
for workflow in data['workflows']:
    print(f"- {workflow['name']}")
```

---

## 📝 Notas Importantes

1. **Codificação de URL**: Sempre encode o nome da categoria na URL

   - ✅ `Communication%20%26%20Messaging`
   - ❌ `Communication & Messaging`

2. **Case Sensitive**: O nome da categoria deve corresponder **exatamente** ao que está no JSON

   - ✅ `"AI Agent Development"`
   - ❌ `"ai agent development"` ou `"AI AGENT DEVELOPMENT"`

3. **Performance**: Este endpoint é mais rápido que `/api/workflows/category/` pois usa SQL IN ao invés de múltiplos LIKE

4. **Manutenção**: Para adicionar/remover workflows de categorias, edite `context/search_categories.json`

---

## 🔄 Atualização de Categorias

Para categorizar novos workflows:

1. Edite `context/search_categories.json`
2. Adicione entrada:
   ```json
   {
     "filename": "novo_workflow.json",
     "category": "Business Process Automation"
   }
   ```
3. Não precisa reiniciar o servidor (arquivo é lido a cada requisição)

---

## 🎯 Próximos Passos

- [ ] Adicionar cache para `search_categories.json`
- [ ] Criar endpoint para listar workflows sem categoria
- [ ] Implementar sugestão automática de categorias baseada em IA
- [ ] Adicionar endpoint para atualizar categorias via API
