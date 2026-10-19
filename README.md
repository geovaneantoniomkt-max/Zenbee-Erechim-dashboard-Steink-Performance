# ZenBee Mobi × Steink Performance — Dashboard de performance

Dashboard protegido por senha com os dados de **Meta Ads** da ZenBee Mobi Erechim (a ZenBee não roda
Google Ads). Publicado no **Cloudflare Pages** (`zenbee-erechim-dashboard.pages.dev`). Feito a partir do
modelo da Nohotel — mesmo visual, mesma camada de senha, mesmos coletores.

| Item | Valor |
|---|---|
| Conta Meta Ads | `1980738282592067` — "ZenBee Mobi Erechim" (Business `1847399216247431`, "ZenBee - Erechim") |
| Página do Facebook | `1271112742762331` — "ZenBee Mobi Erechim" |
| Pixel | `1640597037575852` — "Pixel - ZenBee - Erechim" |
| Instagram | ID ainda não informado (`META_IG_USER_ID`) — sem ele a aba Orgânico fica escondida |
| Praça | Erechim e região (RS) |

## Seções

| Seção | O que mostra |
|---|---|
| Visão executiva | Verba do mês e ritmo de gasto, divisão da verba entre os objetivos, KPIs com variação vs. período anterior (acessos ao link de download, visitas ao perfil, novos seguidores, cliques, alcance), gráficos diários, histórico mês a mês, melhores criativos, dinheiro parado e **alertas priorizados por dinheiro em jogo** |
| Meta Ads | Campanhas e conjuntos com status, orçamento, resultado, custo por resultado vs. meta e ação recomendada; idade/gênero e posicionamento por objetivo (30 dias) |
| Criativos | Cards por anúncio com miniatura, gasto, resultados, custo, CTR, CPM, seguidores e link para o vídeo publicado |
| Legendas | O que significa cada métrica, status e regra de qualidade |

As abas **Google Ads** e **Orgânico** ficam escondidas: Google está desligado em `public/config.json`
(`google_ads.enabled: false`) e o Orgânico aparece sozinho quando o coletor gerar `organic.json`.

## O que conta como resultado

O dashboard lê o objetivo de cada conjunto de anúncios e usa isso para decidir o que é "resultado":

| Campanha | Objetivo do conjunto | Resultado exibido | Meta |
|---|---|---|---|
| `[PS] [TRAFEGO] [DOWNLOAD] [LINKTREE]` | Visualizações da página de destino | Acessos ao link de download | R$ 0,20 |
| `[PS] [TRAFEGO] [IG]` | Visitas ao perfil do Instagram | Visitas ao perfil | R$ 0,30 |
| (as duas) | — | Novos seguidores no Instagram | R$ 1,00 |

As metas saíram dos 12 primeiros dias da conta (08 a 19/10/2026): mediana diária de R$ 0,18 por acesso,
R$ 0,26 por visita e R$ 0,80 por seguidor, arredondadas para cima porque o histórico ainda é curto.
Revisar depois de 30 dias. São editáveis no menu lateral (ficam salvas só no navegador de quem editou);
o padrão fica em `public/config.json`.

> **Acesso ao link não é download.** A campanha de download leva até o Linktree com os links das lojas;
> o Meta conta quem chegou lá, não quem instalou. Para medir instalações: números da Play Console /
> App Store Connect, ou o SDK do Meta no app (e aí otimizar a campanha por instalação).

## Publicar e atualizar

Passo a passo completo em [`DASHBOARD.md`](DASHBOARD.md). Resumo:

```bash
python scripts/fetch_meta.py          # coleta (precisa de META_ACCESS_TOKEN)
python scripts/bundle_cloudflare.py   # gera deploy-cloudflare/ e deploy-cloudflare.zip
npm test                              # 35 verificações da senha, inclusive no _worker.js gerado
```

Cloudflare → **Workers & Pages → Create → Pages → Upload assets** → arrastar a pasta
`deploy-cloudflare` (ou o `.zip`). Nunca arraste a `public/` sozinha: o upload pelo painel não roda a
pasta `functions/`, e o site subiria **sem senha**.

## Estrutura

```
public/                       site estático (index.html, app.js, styles.css, config.json, logo.jpg)
public/data/                  JSONs gerados pelos coletores — ignorados pelo git
functions/_middleware.js      senha, sessão e cabeçalhos de segurança (Cloudflare Pages)
scripts/bundle_cloudflare.py  monta deploy-cloudflare/ com o _worker.js para o upload pelo painel
scripts/fetch_meta.py         coletor do Meta Ads + orgânico
scripts/cache_images.py       baixa as miniaturas dos criativos para o próprio site
.github/workflows/            update-dashboard.yml — coleta + testes + deploy 3x por dia
netlify/, netlify.toml        a mesma proteção em formato Netlify (caminho alternativo do modelo)
PLAYBOOK-NOVO-CLIENTE.md      como montar este dashboard para outro cliente
```

> Este repositório é público. Nenhum token, senha ou dado do cliente entra no git: `public/data/`,
> `deploy-cloudflare/` e os arquivos `.env*` estão no `.gitignore`.
