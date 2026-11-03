# Empório da Música

## Technical Project Documentation

**Document type:** Prototype technical documentation  
**Application:** Text-based customer service agent  
**Language of the application:** Brazilian Portuguese  
**Data classification:** Fictional demonstration data

## 1. Purpose and scope

Empório da Música is a local customer-service prototype for a fictional musical-instrument store. It provides grounded answers about the catalog, orders, promotions, and store policies through an interactive command-line interface.

The project prioritizes:

- predictable behavior without external services;
- answers grounded in local data;
- explicit intent routing;
- simple installation and reproducibility;
- a clear fallback when the requested information is unavailable.

The application is not a production commerce platform. It does not authenticate customers, connect to a real order-management system, or expose a web API.

## 2. Functional behavior

### Supported intents

| Intent | Example | Main source |
|---|---|---|
| `GREETING` | `oi` | Fixed persona response |
| `PRODUCT_INFO` | `qual o preço da guitarra Yamaha FG800?` | Product and promotion CSVs |
| `ORDER_STATUS` | `qual o status do pedido #1?` | Orders, customers, order-items, and products CSVs |
| `POLICY` | `aceitam pix?` | Store policy PDF |
| `OUT_OF_SCOPE` | `vocês vendem cabos?` | Router keyword rules |
| `UNKNOWN` | An unsupported or ambiguous question | Fixed fallback response |

### Product responses

The product flow can return the product name, price, description, stock quantity, catalog status, and an active promotion when available. Products are found by product ID or by a case-insensitive substring of their name. Category and maximum-price filters are also supported, for example `quais violões custam até R$ 1.000?`; matching products are returned in ascending price order.

### Order responses

The order flow can return the customer name, order status, total, tracking code, estimated delivery, and the products and quantities associated with the order. The order number is extracted from the message with a regular expression.

### Policy responses

The policy flow extracts text from `data/políticas_da_loja.pdf`, divides it into sections, and searches for topic keywords. Supported topics include opening hours, exchanges and returns, payments, warranty, shipping, privacy, and discounts.

### Out-of-scope responses

Accessory keywords such as cables, picks, cases, pedals, tuners, and amplifiers take priority over product classification. This prevents the agent from presenting an unsupported accessory as a catalog product.

## 3. Technical architecture

```text
User
  |
  v
cli.py
  |
  v
agent.py
  |
  +--> intent_router.py ------> Intent + extracted entities
  |
  +--> knowledge_base.py -----> In-memory indexes and grounded lookup
             |
             v
       data_loader.py
          |        |
          v        v
        CSV files  Policy PDF
```

### Module responsibilities

- `cli.py`: reads user input, handles exit/help commands, and prints responses.
- `agent.py`: maps intents to handlers and owns fixed fallback/persona messages.
- `intent_router.py`: performs keyword classification and extracts order IDs, product queries, policy topics, and out-of-scope items.
- `data_loader.py`: reads all CSV files with BOM-safe UTF-8 and extracts PDF text.
- `knowledge_base.py`: builds indexes and formats product, order, and policy results.
- `conversation_history.py`: persists up to 100 conversation exchanges in JSON.
- `test_agent.py`: exercises representative classifications and responses.

## 4. Data flow

1. `KnowledgeBase` calls `load_all()` during agent initialization.
2. The loader reads six CSV files from `data/`.
3. The policy PDF is extracted with `pdfplumber`; `pypdf` is used as a fallback when needed.
4. The knowledge base builds indexes by product ID, product name, order ID, customer ID, customer name, order items, and product promotions.
5. Each user message is classified before any lookup.
6. The matching handler queries only the relevant in-memory data.
7. The agent formats a Portuguese response or returns a specific fallback.

## 5. Framework and agent approach

The project uses a deliberately small **hybrid approach**:

- deterministic intent classification and entity extraction;
- structured retrieval from CSV files;
- keyword-based retrieval from the policy PDF;
- deterministic response templates for reliable facts;
- optional local LLM rewriting through Ollama.

This approach was chosen over ReAct, function calling, and a SQL agent because the data set is small and known in advance. Explicit handlers make prices, stock, orders, and policies easier to audit and test.

## 6. Model and provider

The default provider is the local deterministic pipeline: no model, API key, network connection, or paid service is required. The optional provider is **Ollama**, accessed through its local HTTP endpoint.

The default Ollama model is `llama3.2:latest`. It can be changed with `--ollama-model` or the `OLLAMA_MODEL` environment variable. The endpoint defaults to `http://127.0.0.1:11434` and can be changed with `OLLAMA_URL`.

The LLM is not the source of truth. It only rewrites an answer already grounded in local data. If Ollama is unavailable, the model fails, or a factual response is not safely preserved, the deterministic answer is returned.

## 7. Retrieval architecture and design choices

The implementation uses deterministic retrieval rather than a vector database because the data set is small, local, and highly structured. This keeps price, stock, and order responses auditable and avoids arbitrary SQL or tool calls generated by a model.

Structured records are indexed in memory by IDs and names. Policy text is extracted from the PDF and searched by topic keywords. Product category and maximum-price filters are applied directly to structured fields such as `category_id` and `price_brl`.

## 8. Prompt strategy

When `--ollama` is enabled, the prompt contains the customer's original question, the deterministic answer retrieved from local data, instructions to answer in Brazilian Portuguese, and an instruction not to add prices, addresses, policies, or availability not present in the grounded answer.

The model has a wording role rather than a retrieval or database-query role. This reduces hallucination risk and keeps local data authoritative.

## 9. Installation and execution

```bash
python -m venv .venv
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

To run the smoke test:

```bash
python test_agent.py
```

The repository's essential behavior is local and reproducible. The CSV files and policy PDF must remain in the `data/` directory.

Run without Ollama:

```bash
python cli.py
```

To enable optional local Ollama response wording, start Ollama and run `python cli.py --ollama`. Use `--ollama-model` to select another installed model. If the local service is unavailable, the deterministic response is retained.

```bash
python cli.py --ollama
python cli.py --ollama --ollama-model gemma3:latest
```

## 10. CLI usage

The CLI accepts free-text questions in Brazilian Portuguese. It also recognizes:

- `/ajuda` and `/help`;
- `/historico`;
- `/limpar`;
- `/status`;
- `/debug <question>`;
- `/sair`, `/exit`, and `/quit`.

`--check` validates that the required CSV tables and policy PDF are loaded without starting the interactive interface:

```bash
python cli.py --check
```

Conversation history is stored by `conversation_history.py`, and the CLI exposes history inspection and clearing commands.

Example:

```text
Você: tem violão Tagima em estoque?
Agente: [catalog response based on the loaded CSV data]
```

## 11. Persistence and privacy considerations

The conversation history is written to `conversation_history.json` in the project directory. It contains user messages and generated responses and is limited to the latest 100 exchanges.

Because there is no authentication or user separation, this persistence design is suitable only for local demonstrations. A production implementation should use authenticated access, controlled retention, encryption where appropriate, and a transactional data store.

## 12. Technical trade-offs

### Deterministic routing instead of an autonomous agent

The data set is small and known in advance, so explicit handlers make answers auditable and reproducible. This reduces hallucinations and avoids arbitrary database queries. The trade-off is less flexibility with ambiguous or unforeseen wording.

### Ollama instead of a hosted API

Ollama runs locally without credentials or per-request cost and keeps demonstration data on the local machine. The trade-off is dependence on local hardware and model availability.

### CLI instead of a web UI

The challenge explicitly allows a CLI. It keeps the focus on agent behavior and retrieval quality and is easy to reproduce. The trade-off is a less polished end-user experience than a web interface.

### JSON history instead of a database

JSON is dependency-free and appropriate for a single-user prototype. The trade-off is no multi-user isolation, transactions, or concurrent-write protection.

## 13. Testing strategy

`test_agent.py` is a lightweight smoke test covering:

- greetings;
- product questions;
- order questions;
- policy questions;
- out-of-scope accessories;
- unknown messages.

Run it after installation with:

```bash
python test_agent.py
```

Future test coverage should include malformed CSV values, missing files, empty messages, ambiguous intents, unknown product and order IDs, policy extraction failures, and history write failures.

## 14. Known limitations and production considerations

This prototype intentionally omits:

- customer authentication and authorization;
- real-time inventory and order integration;
- a web or API layer;
- concurrency-safe conversation storage;
- semantic search and reranking;
- comprehensive automated tests;
- monitoring, metrics, and alerting;
- production-grade error reporting.
- Ollama response quality depends on the selected local model and available hardware.

Before production use, these concerns should be addressed together with data validation, structured logging, privacy controls, and a deployment strategy.

## 15. Use of coding assistants

**Copilot SDK in VS Code** was used as a development assistant. The workflow was to inspect the repository, reproduce behavior, investigate bugs, evaluate implementation options, apply focused changes, review the generated code manually, run tests and syntax checks, and organize the README and technical documentation.

Copilot did not replace validation or design decisions. The implementation, test results, local Ollama behavior, and final documentation were checked in the repository environment.

## 16. Repository map

| Path | Responsibility |
|---|---|
| `agent.py` | Agent orchestration and response handlers |
| `cli.py` | Interactive terminal interface |
| `data_loader.py` | CSV and PDF loading |
| `knowledge_base.py` | Data normalization and lookups |
| `intent_router.py` | Intent and entity extraction |
| `conversation_history.py` | Local conversation persistence |
| `test_agent.py` | Smoke tests |
| `data/` | Fictional source data |
| `examples/` | Example conversations |

## 17. Responsible use

The included customer, product, order, and policy information is fictional. Do not use the repository as a source of real customer decisions or as a substitute for authenticated operational systems.
