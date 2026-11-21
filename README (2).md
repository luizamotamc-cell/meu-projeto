# Cotações e Clima

Projeto com duas aplicações que consomem APIs públicas:

1. **Cotações** — página web que mostra a cotação de moedas em reais e converte valores entre elas. API: [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas).
2. **Clima** — aplicação em Python que busca a temperatura de uma cidade, salva num banco SQL (SQLite) e exibe o histórico num site com gráfico. API: [Open-Meteo](https://open-meteo.com/).

Nenhuma das duas APIs exige chave de acesso.

## Estrutura

```
meu-projeto/
├── cotacoes/
│   └── index.html          página de cotações (HTML + JavaScript)
├── clima/
│   ├── app.py              site Flask (página, API JSON e rota de coleta)
│   ├── clima.py            consulta à API e funções do banco SQL
│   ├── schema.sql          estrutura da tabela e exemplos de consultas
│   ├── rodar_clima.bat     coleta automática no Windows
│   ├── requirements.txt    dependências Python
│   └── Procfile            comando de inicialização para hospedagem
├── .gitignore
└── README.md
```

## Cotações

Não precisa instalar nada. Dê dois cliques em `cotacoes/index.html` e a página abre no navegador.

Para mudar as moedas exibidas, edite o objeto `MOEDAS` no início do script.

## Clima

Requisitos: Python 3.9 ou superior.

### Rodar no PowerShell

```powershell
cd clima
pip install flask

# Defina uma senha para a rota de coleta (invente a sua; vale só para esta janela)
$env:COLETA_TOKEN = "minhasenha123"

python app.py
```

Com o servidor rodando, abra no navegador:

- `http://127.0.0.1:5000/coletar?token=minhasenha123` para registrar uma leitura
- `http://127.0.0.1:5000/` para ver a temperatura atual, o gráfico e o histórico

Também dá para coletar sem o navegador, em outra janela do PowerShell:

```powershell
Invoke-RestMethod "http://127.0.0.1:5000/coletar?token=minhasenha123"
```

Para usar só o script de terminal, sem o site:

```powershell
python clima.py                   # Campinas (padrão)
python clima.py "Rio de Janeiro"  # outra cidade
python clima.py --historico       # mostra as leituras salvas
```

### Variáveis de ambiente

| Variável       | Para que serve                         | Padrão     |
|----------------|----------------------------------------|------------|
| `COLETA_TOKEN` | senha que protege a rota `/coletar`    | (nenhuma)  |
| `CIDADE`       | cidade monitorada pelo site            | Campinas   |
| `CLIMA_DB`     | caminho do arquivo SQLite              | clima.db   |

### Coleta automática no Windows

O arquivo `rodar_clima.bat` coleta uma leitura e grava em `clima.db`. Agende-o de hora em hora (ajuste o caminho):

```powershell
schtasks /create /tn "ClimaCampinas" /tr "C:\caminho\para\clima\rodar_clima.bat" /sc hourly /mo 1
```

Para remover: `schtasks /delete /tn "ClimaCampinas" /f`

## Publicar na internet

**Cotações:** é um site estático. No GitHub, vá em *Settings → Pages*, escolha a branch principal e a pasta raiz. A página fica em `https://SEU_USUARIO.github.io/NOME_DO_REPO/cotacoes/`.

**Clima:** precisa de um serviço que rode Python (Render, Railway, PythonAnywhere). Exemplo no Render:

1. Crie um *Web Service* ligado ao repositório e defina **Root Directory** como `clima`.
2. *Build Command*: `pip install -r requirements.txt`
3. *Start Command*: `gunicorn app:app`
4. Em *Environment*, crie `COLETA_TOKEN` com uma senha longa e aleatória. Para gerar uma:
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(24))"
   ```
5. Agende uma chamada de hora em hora (por exemplo no cron-job.org) para `https://SEU-APP.onrender.com/coletar?token=SUA_SENHA`.

**Atenção ao banco:** em planos gratuitos de alguns serviços o disco é temporário, e o `clima.db` pode ser apagado quando o serviço reinicia. Para guardar o histórico de forma permanente, use um serviço que mantenha arquivos (como o PythonAnywhere) ou troque o SQLite por PostgreSQL.

## Segurança

- Nunca coloque o `COLETA_TOKEN` real no código nem no repositório. Use sempre variável de ambiente.
- O `.gitignore` já impede que `clima.db` e `log.txt` sejam enviados ao GitHub.
