# Configuração do dashboard — ZenBee Mobi

```
GitHub Actions (3x/dia: 06h, 12h, 18h BRT)                  Cloudflare Pages
┌────────────────────────────────┐  wrangler deploy  ┌──────────────────────────────────┐
│ scripts/fetch_meta.py          │ ────────────────► │ functions/_middleware.js         │ ← senha + cabeçalhos
│   META_ADS_TOKEN (secret)      │  public/ + data/  │ public/index.html, app.js        │
│   → public/data/meta.json      │ (nunca vai p/ git)│ public/data/*.json               │ ← só com sessão válida
│ scripts/cache_images.py        │                   └──────────────────────────────────┘
└────────────────────────────────┘
```

Enquanto a automação não estiver ligada, o site é publicado à mão pelo painel do Cloudflare (passo 1).
Os dois caminhos usam o mesmo projeto e a mesma senha.

## 1. Primeira publicação (upload pelo painel)

1. Gere o pacote (já com os dados coletados em `public/data/`):

   ```bash
   python scripts/bundle_cloudflare.py
   ```

   Ele cria `deploy-cloudflare/` e `deploy-cloudflare.zip` com o site, os dados e um `_worker.js` — a
   camada de senha gerada de `functions/_middleware.js`. O upload pelo painel **não compila a pasta
   `functions/`**; o `_worker.js` é o que ele aceita. Rode `npm test` para conferir a senha nele também.

2. Cloudflare → **Workers & Pages → Create → Pages → Upload assets**.
   - **Project name:** `zenbee-erechim-dashboard` (é o nome que o workflow e o `wrangler.toml` esperam;
     se usar outro, crie a variável `CF_PAGES_PROJECT` no GitHub com o nome escolhido).
   - Arraste a pasta `deploy-cloudflare` (ou o `.zip`) e clique em **Deploy site**.

3. **Settings → Variables and Secrets** (ambiente *Production*), tipo **Secret**:

   | Variável | Valor |
   |---|---|
   | `DASHBOARD_PASSWORD` | a senha que a equipe vai digitar (16+ caracteres) |
   | `SESSION_SECRET` | string aleatória longa — assina o cookie de sessão |
   | `SESSION_HOURS` | opcional, duração da sessão em horas (padrão 12) |

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"   # gera um SESSION_SECRET
   ```

4. **Suba de novo** (Deployments → *Create deployment* → mesma pasta). Variável nova só vale no
   deploy seguinte. Até lá o site responde **503 em tudo** — de propósito: fechado, nunca aberto.

5. Confira: `https://zenbee-erechim-dashboard.pages.dev/` redireciona para `/login`, e
   `https://zenbee-erechim-dashboard.pages.dev/data/meta.json` responde **401** sem login.

| O que arrastar | O que acontece |
|---|---|
| `public/` sozinha | Sobe **sem senha**, com os dados do cliente abertos. Nunca faça isso. |
| A pasta do projeto inteira | Sobe `node_modules` e os arquivos locais de segredo. |
| **`deploy-cloudflare`** | Site + dados + `_worker.js` com a senha. É o que você quer. |

## 2. Atualização automática (GitHub Actions)

Em **Settings → Secrets and variables → Actions → New repository secret**:

| Nome | O que é |
|---|---|
| `META_ADS_TOKEN` | token do Usuário do Sistema com acesso à conta `1980738282592067` e à página `1271112742762331` |
| `CLOUDFLARE_API_TOKEN` | Cloudflare → My Profile → API Tokens → modelo **Edit Cloudflare Workers** (ou permissão *Cloudflare Pages: Edit*) |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare → Workers & Pages → Account ID (coluna da direita) |

Variáveis opcionais (aba *Variables*): `META_IG_USER_ID` (ID do Instagram Business — liga a aba
Orgânico), `CF_PAGES_PROJECT` (se o projeto não se chamar `zenbee-erechim-dashboard`),
`META_SINCE` (padrão `2026-10-01`), `META_API_VERSION` (padrão `v23.0`).

O workflow `.github/workflows/update-dashboard.yml` roda 3x por dia (06:17, 12:17 e 18:17 de Brasília),
manualmente em **Actions → Atualizar dashboard → Run workflow** e a cada push na `main` que altere o
site. Sem os secrets ele só avisa e termina, sem falhar. Com eles: coleta, baixa as miniaturas, roda os
testes da senha, publica com `wrangler` (que compila `functions/` direto) e confere na URL que os dados
continuam respondendo 401 sem sessão.

### Token do Meta — a armadilha mais comum

O token de Usuário do Sistema só enxerga as contas que **aquele usuário** recebeu. Business Manager →
Usuários → **Usuários do Sistema** → selecione o usuário → **Adicionar ativos** → marque a conta de
anúncios `1980738282592067`, a página "ZenBee Mobi Erechim" e o Instagram, com permissão de leitura.
Escopos: `ads_read` · `business_management` · `pages_read_engagement` · `pages_show_list` ·
`read_insights` · `instagram_basic` · `instagram_manage_insights`.

## 3. Rodar localmente

```bash
set META_ACCESS_TOKEN=EAAB...        # PowerShell: $env:META_ACCESS_TOKEN="EAAB..."
python scripts/fetch_meta.py
npm run dev:cloudflare               # http://localhost:8790 (lê a senha de .dev.vars)
```

## 4. Segurança

- Tokens só existem como *secrets* do GitHub; o site publicado não contém token nenhum.
- Dados nunca entram no git (`public/data/`, `deploy-cloudflare/` no `.gitignore`) — o repositório é público.
- Tudo atrás de senha, inclusive os JSONs. Sessão em cookie assinado (HMAC-SHA256), `HttpOnly`,
  `Secure`, `SameSite=Strict`, 12 h. Bloqueio de 15 min após 5 erros por IP, proteção CSRF, sem
  *open redirect*, CSP estrita, HSTS, `X-Frame-Options: DENY`, `noindex`.
- Sem `DASHBOARD_PASSWORD`/`SESSION_SECRET` o site responde 503 em vez de abrir.
- Trocar a senha sempre que alguém sair do projeto. Trocar o `SESSION_SECRET` derruba todas as sessões.
