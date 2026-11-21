
"""Mini aplicação web do clima.

Rotas:
    /                 página com a temperatura atual, gráfico e tabela
    /api/leituras     as mesmas leituras em JSON (?limite=48)
    /coletar?token=X  busca uma nova leitura na API e salva no banco

Variáveis de ambiente (todas opcionais, exceto COLETA_TOKEN para usar /coletar):
    CIDADE        cidade monitorada (padrão: Campinas)
    CLIMA_DB      caminho do arquivo SQLite (padrão: clima.db)
    COLETA_TOKEN  senha que protege a rota /coletar
"""
import hmac
import os
import sqlite3
import urllib.error

from flask import Flask, abort, jsonify, render_template_string, request

import clima

clima.BANCO = os.environ.get("CLIMA_DB", "clima.db")
CIDADE = os.environ.get("CIDADE", "Campinas")
TOKEN = os.environ.get("COLETA_TOKEN", "")

app = Flask(__name__)


def ler_leituras(limite=48):
    """Devolve as últimas leituras, da mais antiga para a mais recente."""
    conexao = clima.conectar()
    conexao.row_factory = sqlite3.Row
    try:
        linhas = conexao.execute(
            """SELECT id, cidade, temperatura_c, umidade, vento_kmh, medido_em
               FROM leituras ORDER BY id DESC LIMIT ?""",
            (limite,),
        ).fetchall()
    finally:
        conexao.close()
    return [dict(l) for l in reversed(linhas)]


PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clima em {{ cidade }}</title>
<style>
  :root { --bg:#f3f5f7; --surface:#fff; --ink:#14202b; --muted:#5b6b79; --line:#d9e0e6; --accent:#c2410c; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#0f171e; --surface:#17222b; --ink:#e8eef2; --muted:#93a3b0; --line:#263540; --accent:#fb923c; }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; line-height:1.5; }
  main { max-width:760px; margin:0 auto; padding:32px 16px 56px; }
  h1 { font-size:1.5rem; margin:0 0 4px; }
  .sub { color:var(--muted); margin:0 0 24px; font-size:.95rem; }
  section { background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:20px; margin-bottom:20px; }
  h2 { font-size:1.05rem; margin:0 0 14px; }
  .agora { font-size:3.5rem; font-weight:700; letter-spacing:-.02em; color:var(--accent); line-height:1; }
  .detalhes { color:var(--muted); margin-top:8px; }
  table { width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }
  th, td { text-align:right; padding:8px 6px; border-bottom:1px solid var(--line); }
  th:first-child, td:first-child { text-align:left; }
  th { font-weight:500; color:var(--muted); font-size:.85rem; }
  tr:last-child td { border-bottom:0; }
  .vazio { color:var(--muted); }
  .grafico { position:relative; height:260px; }
</style>
</head>
<body>
<main>
  <h1>Clima em {{ cidade }}</h1>
  <p class="sub">Dados da Open-Meteo, coletados periodicamente e guardados em SQL.</p>

  {% if leituras %}
  {% set ultima = leituras[-1] %}
  <section>
    <div class="agora">{{ "%.1f"|format(ultima.temperatura_c) }}°C</div>
    <div class="detalhes">Umidade {{ ultima.umidade }}% · vento {{ "%.1f"|format(ultima.vento_kmh) }} km/h · medido em {{ ultima.medido_em.replace("T", " ") }}</div>
  </section>

  <section>
    <h2>Temperatura nas últimas leituras</h2>
    <div class="grafico"><canvas id="grafico" role="img" aria-label="Gráfico de temperatura ao longo do tempo"></canvas></div>
  </section>

  <section>
    <h2>Histórico</h2>
    <table>
      <thead><tr><th>Medido em</th><th>Temperatura</th><th>Umidade</th><th>Vento</th></tr></thead>
      <tbody>
      {% for l in leituras|reverse %}
        <tr><td>{{ l.medido_em.replace("T", " ") }}</td><td>{{ "%.1f"|format(l.temperatura_c) }}°C</td><td>{{ l.umidade }}%</td><td>{{ "%.1f"|format(l.vento_kmh) }} km/h</td></tr>
      {% endfor %}
      </tbody>
    </table>
  </section>
  {% else %}
  <section><p class="vazio">Ainda não há leituras salvas. Acesse /coletar?token=SEU_TOKEN para registrar a primeira.</p></section>
  {% endif %}
</main>

{% if leituras %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
  const dados = {{ leituras|tojson }};
  const cor = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();
  new Chart(document.getElementById("grafico"), {
    type: "line",
    data: {
      labels: dados.map(d => d.medido_em.slice(5).replace("T", " ")),
      datasets: [{ label: "°C", data: dados.map(d => d.temperatura_c), borderColor: cor, backgroundColor: cor, tension: 0.3, pointRadius: 2 }]
    },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { maxTicksLimit: 8 } } } }
  });
</script>
{% endif %}
</body>
</html>
"""


@app.route("/")
def inicio():
    return render_template_string(PAGINA, cidade=CIDADE, leituras=ler_leituras())


@app.route("/api/leituras")
def api_leituras():
    limite = min(max(request.args.get("limite", 48, type=int), 1), 500)
    return jsonify(ler_leituras(limite))


@app.route("/coletar")
def coletar():
    enviado = request.args.get("token", "")
    if not TOKEN or not hmac.compare_digest(enviado, TOKEN):
        abort(403)
    try:
        cidade = clima.buscar_cidade(CIDADE)
        leitura = clima.buscar_clima(cidade)
    except ValueError as erro:
        return jsonify(erro=str(erro)), 404
    except (urllib.error.URLError, TimeoutError):
        return jsonify(erro="Não foi possível acessar a API de clima."), 502
    conexao = clima.conectar()
    try:
        clima.salvar(conexao, cidade, leitura)
    finally:
        conexao.close()
    return jsonify(cidade=cidade["cidade"], **leitura)


if __name__ == "__main__":
    app.run(debug=True)
