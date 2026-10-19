#!/usr/bin/env python3
"""
Monta uma pasta (e um .zip) para subir no Cloudflare Pages arrastando pelo painel
(Workers & Pages → Create → Pages → "Upload assets", o Direct Upload).

Por que existe: o upload pelo painel do Cloudflare NÃO compila a pasta functions/. Arrastar a
public/ sozinha publica o dashboard SEM a camada de senha, com os dados do cliente abertos.
O que o upload pelo painel aceita é um único arquivo _worker.js na raiz (modo "advanced" do
Pages). Este script gera esse _worker.js a partir de functions/_middleware.js — o mesmo código
coberto por tests/auth.test.mjs — e junta com a public/ e os dados já coletados:

    deploy-cloudflare/
        _worker.js        camada de senha (gerada de functions/_middleware.js; não é servido)
        index.html, app.js, styles.css, config.json, logo.jpg ...
        data/meta.json    dados (só passam com sessão válida)

Uso:
    python scripts/bundle_cloudflare.py              # gera ./deploy-cloudflare e ./deploy-cloudflare.zip
    python scripts/bundle_cloudflare.py --out X      # gera em outro lugar
    npm test                                         # roda a bateria de senha também no _worker.js gerado

Depois: arrastar a pasta (ou o .zip) no Cloudflare e cadastrar DASHBOARD_PASSWORD e
SESSION_SECRET em Settings → Variables and Secrets (Production). Sem elas o site responde 503 em
tudo, de propósito. Variável nova só vale no deploy seguinte: depois de cadastrar, suba de novo.

O deploy automático (GitHub Actions + wrangler) não usa este script: o wrangler compila a
functions/ direto.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

MIDDLEWARE = "functions/_middleware.js"
EXPORT = "export async function onRequest(context)"
# nunca copiar, mesmo que apareçam dentro de public/
PROIBIDOS = {".env", ".env.google", ".env.meta", ".dev.vars", "senha-local.txt", "node_modules", "__pycache__", ".gitkeep"}

ENTRADA = """

/* ------------------------------------------------- entrada do _worker.js (gerada) */
// No modo "advanced" do Cloudflare Pages este arquivo recebe TODAS as requisições.
// Os arquivos estáticos vêm de env.ASSETS — o equivalente ao next() do middleware.
export default {
  async fetch(request, env) {
    return onRequest({ request, env, next: () => env.ASSETS.fetch(request) });
  },
};
"""


def gerar_worker() -> str:
    texto = open(MIDDLEWARE, encoding="utf-8").read()
    if texto.count(EXPORT) != 1:
        raise SystemExit(f"ERRO: não encontrei `{EXPORT}` em {MIDDLEWARE}")
    texto = texto.replace(EXPORT, EXPORT.replace("export ", "", 1))
    # um módulo de Worker só pode ter o export default; qualquer outro export quebraria o deploy
    sobra = re.findall(r"^export .*$", texto, flags=re.M)
    if sobra:
        raise SystemExit(f"ERRO: {MIDDLEWARE} tem exports que o _worker.js não aceita: {sobra}")
    cabecalho = f"// ARQUIVO GERADO por scripts/bundle_cloudflare.py a partir de {MIDDLEWARE} — não edite aqui.\n"
    return cabecalho + texto + ENTRADA


def limpar(destino: str) -> None:
    """Esvazia a pasta em vez de apagá-la (no Windows, apagar a própria pasta falha se algum
    terminal estiver com ela aberta)."""
    os.makedirs(destino, exist_ok=True)
    for nome in os.listdir(destino):
        alvo = os.path.join(destino, nome)
        if os.path.isdir(alvo) and not os.path.islink(alvo):
            shutil.rmtree(alvo, ignore_errors=True)
        else:
            try:
                os.remove(alvo)
            except OSError:
                pass


def ignorar(_dir, nomes):
    return [n for n in nomes if n.lower() in PROIBIDOS or n.endswith(".pyc")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="deploy-cloudflare")
    ap.add_argument("--sem-dados", action="store_true", help="permite gerar sem public/data/meta.json")
    args = ap.parse_args()

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(raiz)

    for caminho in (MIDDLEWARE, "public/index.html"):
        if not os.path.exists(caminho):
            print("ERRO: não encontrei", caminho)
            return 2
    if not os.path.exists("public/data/meta.json") and not args.sem_dados:
        print("ERRO: public/data/meta.json não existe — o dashboard subiria vazio.")
        print("      Rode a coleta antes (python scripts/fetch_meta.py) ou use --sem-dados.")
        return 2

    destino = os.path.abspath(args.out)
    if os.path.commonpath([destino, os.path.abspath("public")]) == os.path.abspath("public"):
        print("ERRO: a pasta de saída não pode ficar dentro de public/")
        return 2

    worker = gerar_worker()
    limpar(destino)
    shutil.copytree("public", destino, ignore=ignorar, dirs_exist_ok=True)
    with open(os.path.join(destino, "_worker.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write(worker)

    zip_path = shutil.make_archive(destino, "zip", destino)

    arquivos = [os.path.relpath(os.path.join(d, n), destino) for d, _, ns in os.walk(destino) for n in ns]
    total = sum(os.path.getsize(os.path.join(destino, a)) for a in arquivos)
    print(f"Pacote pronto: {destino}  ({len(arquivos)} arquivos, {total / 1024:.0f} KB)")
    print(f"Zip:           {zip_path}")
    for a in sorted(arquivos):
        print("   ", a.replace(os.sep, "/"))
    print("\nNo Cloudflare: Workers & Pages → Create → Pages → Upload assets → arraste a pasta ou o .zip.")
    print("Depois cadastre DASHBOARD_PASSWORD e SESSION_SECRET (Settings → Variables and Secrets)")
    print("e suba de novo: variável nova só vale no deploy seguinte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
