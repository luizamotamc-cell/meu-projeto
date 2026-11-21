-- Estrutura do banco SQLite (clima.db).
-- O clima.py já cria esta tabela sozinho; este arquivo serve como documentação.

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
);

-- Exemplos de consultas:

-- Últimas 10 leituras
SELECT cidade, temperatura_c, umidade, medido_em
FROM leituras ORDER BY id DESC LIMIT 10;

-- Temperatura média, mínima e máxima por cidade
SELECT cidade, AVG(temperatura_c) AS media, MIN(temperatura_c) AS minima, MAX(temperatura_c) AS maxima
FROM leituras GROUP BY cidade;
