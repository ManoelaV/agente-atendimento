# agente-atendimento

Agente de atendimento por texto (protótipo) para a **Empório da Música**, loja fictícia de instrumentos musicais localizada em Campo Grande/MS.

O agente auxilia a equipe de atendimento respondendo perguntas recorrentes de clientes via mensagens de texto.

## Funcionalidades

- **Persona alinhada** à identidade e tom da loja (português do Brasil, acolhedor e profissional)
- **Consulta de produtos**: preço, estoque, descrição, status no catálogo e promoções ativas
- **Status de pedido**: rastreio, total, previsão de entrega e itens do pedido
- **Políticas da loja**: horário de funcionamento, formas de pagamento (PIX, cartão, boleto), trocas e devoluções, garantia, frete, privacidade (LGPD)
- **Fora de escopo**: redireciona educadamente pedidos de acessórios que a loja não vende (cordas, palhetas, cabos, cases, pedais, amplificadores)
- **Não entendido**: pede para reformular a pergunta

## Estrutura

```
agente-atendimento/
├── data/                       # Dados da operação (CSVs + manual em PDF)
│   ├── desafio_tecnico_ai_eng - categories.csv
│   ├── desafio_tecnico_ai_eng - customers.csv
│   ├── desafio_tecnico_ai_eng - orders.csv
│   ├── desafio_tecnico_ai_eng - order_items.csv
│   ├── desafio_tecnico_ai_eng - products.csv
│   ├── desafio_tecnico_ai_eng - promotions.csv
│   └── políticas_da_loja.pdf
├── data_loader.py              # Carregador de CSVs e extração de texto do PDF
├── knowledge_base.py           # Base de conhecimento: consultas a dados e políticas
├── intent_router.py            # Roteamento de intenção + extração de entidades
├── agent.py                    # Persona do agente + geração de respostas
├── cli.py                      # Interface de linha de comando para testar
├── test_agent.py               # Testes rápidos de validação
├── requirements.txt            # Dependências Python
├── .gitignore
└── README.md
```

## Como rodar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Executar o agente (CLI interativa)

```bash
python cli.py
```

### 3. Executar testes rápidos

```bash
python test_agent.py
```

## Exemplo de uso

```
Você: qual o preço da guitarra Yamaha FG800?
Agente: *Yamaha FG800 Dreadnought Natural* — R$ 1.299,00
Violão dreadnought Yamaha com tampo sólido em Spruce...
Estoque: 7 unidade(s) disponível(eis).

Você: qual o status do pedido #1?
Agente: Olá, Pedro Henrique Oliveira! Seu pedido #1 está *delivered*.
Total: R$ 11.499,00.
Código de rastreio: BRAB1234567BR.
Previsão de entrega: 2025-10-25.

Você: qual o horário de funcionamento?
Agente: Segunda a Sexta-feira 09:00 às 18:00
Sábado 09:00 às 13:00
Domingo e Feriados Fechado
```

## Tecnologias

- Python 3
- `pypdf` / `pdfplumber` — extração de texto do manual de políticas (PDF)
- Apenas biblioteca padrão + dependências leves (sem LLM externo neste protótipo)