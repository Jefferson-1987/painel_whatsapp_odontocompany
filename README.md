# Painel de Controle Chatbot WhatsApp (Evolution API + Supabase)

Este é um painel de controle desenvolvido em Python (Flask) para gerenciar o status de atendimento de leads armazenados no Supabase.

## Funcionalidades

- **Tela de Login**: Acesso restrito ao operador.
- **Listagem de Leads**: Exibe todos os leads da tabela `costumer`.
- **Destaque Visual**: Leads que aguardam atendimento humano (`active = false`) aparecem com fundo vermelho e no topo da lista.
- **Alternância de Status**: Botão para ativar/desativar o chatbot (muda o campo `active` no Supabase).
- **Ordenação Inteligente**: Leads aguardando atendimento aparecem no topo, ordenados pelos mais recentes.
- **Resumo em Tempo Real**: Exibe o contexto da conversa diretamente no card do lead (armazenado em memória, sem alterar seu Supabase).
- **Ordenação Dinâmica**: Leads que solicitam atendimento humano sobem para o topo na ordem em que os resumos chegam.

## Integração com n8n

Para enviar o resumo da conversa para o painel, use um nó de **HTTP Request** no n8n:

- **Método**: POST
- **URL**: `http://seu-ip-ou-dominio:5000/api/update_summary`
- **Body (JSON)**:
  ```json
  {
    "phone": "5511999999999",
    "summary": "O cliente quer saber sobre preços e prazos de entrega."
  }
  ```
*Nota: O resumo ficará visível no painel enquanto o servidor estiver rodando e o lead estiver com `active=false` no Supabase.*

## Configuração

As configurações estão no arquivo `.env`:
- `SUPABASE_URL`: URL do seu projeto Supabase.
- `SUPABASE_KEY`: Service Role Key para permissão de escrita.
- `ADMIN_USERNAME`: Usuário para login (padrão: admin).
- `ADMIN_PASSWORD`: Senha para login (padrão: admin).

## Como Executar

1. Instale as dependências:
   ```bash
   pip install flask supabase python-dotenv
   ```

2. Execute a aplicação:
   ```bash
   python app.py
   ```

3. Acesse no navegador: `http://localhost:5000`

## Estrutura da Tabela Supabase
O painel espera uma tabela chamada `costumer` com os seguintes campos:
- `cliente_name`: Texto (Nome do cliente)
- `phone`: Texto (ID único/WhatsApp)
- `active`: Booleano (Status do bot)
