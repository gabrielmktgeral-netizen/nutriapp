# NutriApp — MVP

App web (Flask) de registo de refeições e calorias.

## Testar já, sem Notion

Não precisas de nada configurado. Só isto:

```bash
pip install -r requirements.txt
python app.py
```

* Abre http://localhost:5000
* Os dados ficam guardados em `data/local_db.json`, no teu PC
* Podes apagar esse ficheiro a qualquer momento para "recomeçar do zero"
* Quando quiseres ligar ao Notion a sério, segue os passos abaixo

## (Opcional) Ligar ao Notion a sério

## Passo 1 — Criar a integração Notion

* Vai a https://www.notion.so/my-integrations
* Clica "New integration"
* Dá um nome (ex: "NutriApp")
* Copia o "Internal Integration Secret" (começa por `ntn_` ou `secret_`)

## Passo 2 — Partilhar a página com a integração

* Abre a página **"NutriApp - Base de Dados"** no teu Notion (já foi criada com as 5 tabelas: Perfil, Refeições, Despensa, Peso, Exercício)
* Clica "..." → "Connections" → adiciona a integração que criaste

## Passo 3 — Configurar o token

* Copia `.env.example` para `.env`
* Cola o teu token em `NOTION_TOKEN=...`

```bash
cp .env.example .env
# edita o .env e cola o token
```

## Passo 4 — Correr com Notion ligado

```bash
python app.py
```

* A app deteta sozinha o `NOTION_TOKEN` no `.env` e passa a usar o Notion em vez do ficheiro local

## O que já funciona

* Perfil + cálculo automático de calorias/proteína alvo (fórmula Mifflin-St Jeor)
* Registo de refeições por texto (ex: "200g de frango com arroz e uma banana")
* Cálculo automático de kcal/proteína/hidratos/gordura (tabela local de ~50 alimentos comuns em PT)
* Dashboard do dia + calendário semanal
* Despensa virtual + sugestão simples ("o que posso comer agora")
* Registo de peso e exercício

## Limitações desta primeira versão (por design — é o MVP)

* A tabela de alimentos é local e pequena (`food_data.py`) — alimentos não reconhecidos ficam a 0 kcal. Fácil de expandir.
* Sem fotografia, código de barras ou voz ainda — só texto.
* Sem Health Connect (isso exige app Android nativa, é uma fase 2).
* Sem lembretes/notificações ainda.
* Assistente ainda é baseado em regras simples, não IA generativa real.

## Colocar online (sempre disponível, sem PC ligado) — Render.com

Podes colocar online SEM configurar o Notion — fica em modo teste (ficheiro local).

⚠️ Só tens de saber isto: no plano gratuito do Render, o disco é apagado sempre que
o serviço reinicia (cada novo deploy, ou de vez em quando sozinho). Ou seja, os dados
que inseriras podem desaparecer em qualquer altura. Para testar funcionalidades, sem
problema. Quando quiseres dados permanentes, liga ao Notion (passos 1-3 acima) antes
de fazer deploy.

**Passo 1 — Colocar o código no GitHub**
* Cria conta em https://github.com (se não tiveres)
* Cria um repositório novo (ex: "nutriapp")
* Faz upload de todos os ficheiros desta pasta para esse repositório
  (no site do GitHub: "Add file" → "Upload files" → arrasta tudo)

**Passo 2 — Criar conta no Render**
* Vai a https://render.com e cria conta (podes usar login do GitHub)

**Passo 3 — Criar o serviço**
* No Render: "New" → "Web Service"
* Escolhe o repositório "nutriapp" que criaste
* O Render deteta o `render.yaml` automaticamente
* Em "Environment Variables", cola o teu `NOTION_TOKEN`
* Clica "Create Web Service"

**Passo 4 — Pronto**
* Espera 2-3 minutos (build)
* Fica disponível num link tipo `https://nutriapp.onrender.com`
* Funciona no telemóvel, em qualquer rede, com o PC desligado

Nota: no plano gratuito do Render, o servidor "adormece" após uns minutos sem uso e demora
uns segundos a acordar no acesso seguinte — normal, não é erro.

## Próximos passos possíveis

* Ligar a um modelo de IA (ex: API Anthropic/OpenAI) para interpretar texto livre com mais precisão e responder a perguntas abertas ("o que devo comer antes do treino?").
* Expandir tabela de alimentos ou ligar a uma base de dados alimentar (ex: Open Food Facts) para código de barras.
* Notificações push nos horários configurados.
* App Android nativa com Health Connect (fase 2, depois do MVP validado).
