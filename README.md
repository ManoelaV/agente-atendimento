# Agente de atendimento — Empório da Música

Protótipo de um agente de atendimento por texto para a **Empório da Música**, uma loja fictícia de instrumentos musicais localizada em Campo Grande/MS.

O agente responde dúvidas sobre produtos, pedidos e políticas da loja. O foco do projeto é manter as respostas ancoradas nos dados fornecidos, com um fallback local previsível quando um modelo de linguagem não estiver disponível.

## Funcionalidades

- Consulta de preço, descrição, estoque, status de catálogo e promoções de produtos.
- Consulta de status de pedido, total, rastreio, itens e previsão de entrega.
- Consulta das políticas da loja: horário, pagamentos, trocas e devoluções, garantia, frete e privacidade (LGPD).
- Identificação de pedidos fora do escopo, como acessórios que não fazem parte do catálogo.
- Resposta de fallback quando a intenção não é reconhecida ou não há dados suficientes.
- Histórico local das conversas, com comandos para consultar e limpar o histórico.
- Respostas em português do Brasil, com tom acolhedor e profissional.

## Atendimento dos requisitos

O fluxo principal do agente atende aos requisitos do desafio da seguinte forma:

- **Persona da loja:** o agente se apresenta como atendimento da Empório da Música, usa português do Brasil e mantém um tom acolhedor e profissional.
- **Mensagens com contexto:** cada mensagem é classificada e respondida usando os dados carregados dos CSVs, o conteúdo das políticas e, opcionalmente, um modelo local.
- **Consulta adequada:** perguntas sobre produtos e pedidos consultam a base estruturada; perguntas sobre horário, troca, pagamento, garantia, frete e privacidade consultam as políticas da loja.
- **Fora do escopo:** itens não comercializados são identificados antes da classificação de produto e recebem uma resposta explicando o escopo da loja, sem inventar disponibilidade.

## Como rodar

### Pré-requisitos

- Python 3.10 ou superior.
- Os arquivos CSV e o PDF da pasta `data/`.

### Instalação

```bash
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### Executar a interface

```bash
python cli.py
```

Para executar somente com o pipeline local, sem tentar usar Ollama:

```bash
python cli.py --no-ollama
```

Comandos disponíveis na CLI:

- `/ajuda` ou `/help`: mostra exemplos de perguntas.
- `/historico`: mostra as últimas interações.
- `/limpar`: apaga o histórico salvo.
- `/sair`, `/exit` ou `/quit`: encerra a aplicação.

### Executar os testes rápidos

```bash
python test_agent.py
```

## Configuração do modelo e do provedor

O projeto foi desenvolvido para funcionar sem API externa e sem credenciais. O caminho padrão é o pipeline baseado em regras e dados locais. O agente também possui uma integração opcional com **Ollama**, para que uma instalação local possa melhorar a redação da resposta usando o contexto recuperado da base.

Essa integração é deliberadamente opcional:

- não há chave de API nem envio dos dados para um serviço externo;
- `requirements.txt` contém apenas as bibliotecas usadas pelo carregamento do PDF;
- sem Ollama disponível, o agente usa automaticamente as respostas locais;
- `--no-ollama` força esse comportamento e é a forma mais reproduzível de executar o projeto.

Caso o suporte opcional seja usado, é necessário instalar e iniciar o Ollama separadamente, instalar o pacote Python correspondente e ter um modelo local configurado. O nome e a disponibilidade do modelo dependem da instalação local; por isso, o funcionamento essencial do projeto não depende dele.

## Framework e abordagem do agente

Foi escolhida uma abordagem híbrida, combinando **roteamento determinístico de intenção**, uma base de conhecimento local e geração opcional de linguagem:

1. `intent_router.py` classifica a mensagem em `GREETING`, `PRODUCT_INFO`, `ORDER_STATUS`, `POLICY`, `OUT_OF_SCOPE` ou `UNKNOWN`.
2. O roteador extrai entidades simples, como número do pedido, produto e tópico da política, usando palavras-chave e expressões regulares.
3. `knowledge_base.py` consulta os dados estruturados e o texto das políticas.
4. `agent.py` monta um contexto de recuperação específico para a intenção.
5. Se o Ollama estiver disponível, o contexto é enviado ao modelo junto com um prompt de atendimento. Caso contrário, são usadas respostas baseadas em regras.

Não foi usado um agente ReAct, function calling ou agente de SQL. Para este escopo, o roteamento explícito reduz alucinações e torna as consultas de preço, estoque e pedido auditáveis. Também evita que o modelo gere consultas arbitrárias sobre os arquivos.

## Estratégia de recuperação e prompt

O projeto usa uma forma simples de RAG:

- produtos, clientes, pedidos, itens e promoções são carregados dos CSVs;
- o manual de políticas é extraído do PDF com `pdfplumber`, com fallback para `pypdf`;
- produtos e pedidos recebem índices em memória para consultas rápidas;
- textos de busca são normalizados, removendo acentos e espaços inconsistentes;
- somente os registros relevantes à intenção são incluídos no contexto;
- o prompt orienta o modelo a responder em português, ser conciso e não inventar informações ausentes.

Não foi adotado um banco vetorial porque o conjunto de dados é pequeno, local e estruturado. Busca por palavras-chave é suficiente para o protótipo e é mais simples de reproduzir e validar.

## Interface e persistência

A interface é uma **CLI interativa**, adequada ao objetivo de validar o agente sem adicionar complexidade de frontend ou backend.

O histórico é salvo em `conversation_history.json`. Cada registro contém data, mensagem do usuário e resposta do agente. O arquivo é limitado às 100 trocas mais recentes e pode ser limpo com `/limpar`. Essa persistência foi escolhida para manter o contexto entre execuções sem exigir banco de dados.

## Tratamento dos dados

Durante o carregamento, o projeto:

- lê CSVs com `utf-8-sig`, incluindo arquivos com BOM;
- remove chaves vazias;
- normaliza IDs, status, e-mails, preços e quantidades;
- converte valores inválidos para defaults seguros;
- normaliza texto para buscas sem acentos;
- cria índices por ID e nome;
- extrai o texto do PDF e usa uma biblioteca alternativa quando necessário;
- limita a quantidade de produtos adicionados ao contexto do modelo.

Os dados são fictícios e devem ser tratados como dados de demonstração, não como uma base operacional real.

## Estrutura

```text
agente-atendimento/
├── data/                       # CSVs operacionais e manual de políticas em PDF
├── data_loader.py              # Leitura dos CSVs e extração do PDF
├── knowledge_base.py           # Normalização, índices e consultas aos dados
├── intent_router.py            # Classificação de intenção e extração de entidades
├── agent.py                    # Orquestração, contexto, prompt e fallback
├── conversation_history.py     # Persistência local do histórico
├── cli.py                      # Interface de linha de comando
├── test_agent.py               # Testes rápidos de classificação e respostas
├── requirements.txt            # Dependências Python
└── README.md
```

## Exemplo de uso

```text
Você: qual o preço da guitarra Yamaha FG800?
Agente: Yamaha FG800 Dreadnought Natural — R$ 1.299,00
Estoque: 7 unidade(s) disponível(eis).

Você: qual o status do pedido #1?
Agente: Olá, Pedro Henrique Oliveira! Seu pedido #1 está delivered.
Total: R$ 11.499,00.

Você: qual o horário de funcionamento?
Agente: Segunda a Sexta-feira 09:00 às 18:00
Sábado 09:00 às 13:00
Domingo e Feriados Fechado
```

## Exemplos de interação

Foram incluídos quatro exemplos de conversas em [`examples/`](./examples), cobrindo:

- consulta de catálogo e estoque;
- status completo de pedido;
- aplicação da política de troca e devolução;
- tratamento de uma pergunta fora do escopo.

Os exemplos refletem respostas produzidas pelo pipeline local (`python cli.py --no-ollama`). O filtro por faixa de preço, como “violões até R$ 1.000”, ainda não faz parte do protótipo; por isso, esse caso está listado entre as limitações e próximos passos.

## Limitações conhecidas e próximos passos

Este projeto foi desenvolvido em aproximadamente dois dias, por isso o escopo foi mantido como um protótipo funcional e priorizou a entrega do fluxo principal de atendimento.

- O roteamento é baseado em palavras-chave; mensagens ambíguas ou com sinônimos não previstos podem cair em `UNKNOWN`.
- O catálogo ainda não implementa filtros combinados, como listar todos os violões disponíveis até um determinado preço.
- A busca de produtos não é semântica e não usa embeddings ou reranking.
- O histórico é um arquivo JSON local, sem autenticação, concorrência entre processos ou separação por usuário.
- O acesso a pedidos usa o número informado na mensagem; não há autenticação do cliente nem integração com um sistema de pedidos real.
- O tratamento de erros e a interface ainda são adequados a um protótipo, não a um ambiente de produção.
- A integração com Ollama é opcional e depende da configuração do ambiente local.
- Os testes são um smoke test executável, não uma suíte completa de testes unitários e de integração.

Com mais tempo, eu priorizaria testes automatizados para cada intenção e caso-limite, validação de dados na inicialização, autenticação para consultas de pedido, uma API ou UI web, persistência transacional, monitoramento e uma camada de busca híbrida (filtros estruturados + busca semântica) para o catálogo e as políticas.

## Uso de assistentes de código

Foi utilizado o **Copilot SDK no VS Code** como apoio durante o desenvolvimento. A ferramenta foi usada principalmente para investigar e corrigir bugs, sugerir ajustes de implementação e revisar pontos específicos do código, sem substituir a tomada de decisões ou a validação manual.

O workflow foi:

1. reproduzir ou analisar o problema no código;
2. pedir ao Copilot hipóteses para a causa e possíveis correções;
3. aplicar apenas as alterações compatíveis com o escopo do projeto;
4. executar os testes e revisar manualmente o resultado;
5. usar a ferramenta também como apoio para organizar a documentação.

As sugestões geradas foram tratadas como auxílio técnico: o código, os dados e as respostas finais foram conferidos manualmente, e as correções foram validadas pelos comandos de teste do próprio projeto.
