"""Busca a temperatura atual de uma cidade na Open-Meteo e salva num banco SQLite.

Uso:
    python clima.py                 # usa Campinas
    python clima.py "Rio de Janeiro"
    python clima.py --historico     # só mostra o que já foi salvo

Não precisa instalar nada: usa apenas a biblioteca padrão do Python 3.
A Open-Meteo é gratuita e não exige chave de API.
"""
import argparse
import json
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request

BANCO = "clima.db"
URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
URL_CLIMA = "https://api.open-meteo.com/v1/forecast"


def get_json(url, params):
    """Faz uma requisição GET e devolve o JSON da resposta."""
    consulta = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{consulta}", timeout=10) as resposta:
        return json.load(resposta)


def buscar_cidade(nome):
    """Converte o nome da cidade em latitude e longitude."""
    dados = get_json(URL_GEOCODING, {"name": nome, "count": 1, "language": "pt"})
    resultados = dados.get("results")
    if not resultados:
        raise ValueError(f"Cidade não encontrada: {nome}")
    r = resultados[0]
    return {
        "cidade": r["name"],
        "pais": r.get("country", ""),
        "latitude": r["latitude"],
        "longitude": r["longitude"],
        "fuso": r.get("timezone", "auto"),
    }


def buscar_clima(cidade):
    """Pega as condições atuais da cidade."""
    dados = get_json(URL_CLIMA, {
        "latitude": cidade["latitude"],
        "longitude": cidade["longitude"],
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": cidade["fuso"],
    })
    atual = dados["current"]
    return {
        "temperatura_c": atual["temperature_2m"],
        "umidade": atual["relative_humidity_2m"],
        "vento_kmh": atual["wind_speed_10m"],
        "medido_em": atual["time"],
    }


def conectar():
    """Abre o banco e cria a tabela se ela ainda não existir."""
    conexao = sqlite3.connect(BANCO)
    conexao.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            cidade        TEXT    NOT NULL,
            pais          TEXT,
            latitude      REAL    NOT NULL,
            longitude     REAL    NOT NULL,
            temperatura_c REAL    NOT NULL,
            umidade       INTEGER,
            vento_kmh     REAL,
            medido_em     TEXT    NOT NULL,
            coletado_em   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conexao


def salvar(conexao, cidade, clima):
    """Insere uma leitura na tabela."""
    conexao.execute(
        """INSERT INTO leituras
           (cidade, pais, latitude, longitude, temperatura_c, umidade, vento_kmh, medido_em)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (cidade["cidade"], cidade["pais"], cidade["latitude"], cidade["longitude"],
         clima["temperatura_c"], clima["umidade"], clima["vento_kmh"], clima["medido_em"]),
    )
    conexao.commit()


def mostrar_historico(conexao, limite=10):
    """Imprime as últimas leituras salvas."""
    linhas = conexao.execute(
        """SELECT id, cidade, temperatura_c, umidade, vento_kmh, medido_em
           FROM leituras ORDER BY id DESC LIMIT ?""",
        (limite,),
    ).fetchall()
    if not linhas:
        print("Nenhuma leitura salva ainda.")
        return
    print(f"\nÚltimas {len(linhas)} leituras:")
    print(f"{'id':>3}  {'cidade':<18} {'temp':>7} {'umid':>5} {'vento':>9}  medido em")
    for id_, cidade, temp, umid, vento, medido in linhas:
        print(f"{id_:>3}  {cidade:<18} {temp:>5.1f}°C {umid:>4}% {vento:>5.1f}km/h  {medido}")


def main():
    parser = argparse.ArgumentParser(description="Salva a temperatura atual de uma cidade num banco SQLite.")
    parser.add_argument("cidade", nargs="?", default="Campinas", help="nome da cidade (padrão: Campinas)")
    parser.add_argument("--historico", action="store_true", help="só mostra as leituras já salvas")
    args = parser.parse_args()

    conexao = conectar()
    try:
        if not args.historico:
            cidade = buscar_cidade(args.cidade)
            clima = buscar_clima(cidade)
            salvar(conexao, cidade, clima)
            print(f"{cidade['cidade']}, {cidade['pais']}: {clima['temperatura_c']}°C "
                  f"(umidade {clima['umidade']}%, vento {clima['vento_kmh']} km/h) - salvo em {BANCO}")
        mostrar_historico(conexao)
    except ValueError as erro:
        sys.exit(str(erro))
    except (urllib.error.URLError, TimeoutError) as erro:
        sys.exit(f"Não foi possível acessar a API. Verifique sua conexão. ({erro})")
    finally:
        conexao.close()


if __name__ == "__main__":
    main()
