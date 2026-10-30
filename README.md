# Analista ejecutivo de datos con voz — Laboratorio 4

Prototipo local que valida un CSV de ventas, calcula KPIs, genera dos gráficos y produce un resumen ejecutivo en texto (Gemini) y audio (ElevenLabs). Sin claves funciona en modo **SIMULADA**.

## Requisitos
- Python 3.11+ (probado con 3.14.8 en Windows)

## Instalación
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env   # y completa tus claves en .env (nunca lo subas al repo)
```

## Uso
```powershell
.\.venv\Scripts\python.exe data\generate_sample.py   # crea data/sample_sales.csv (200 filas, semilla fija)
.\.venv\Scripts\python.exe -m streamlit run app.py
```
En la app: sube un CSV o marca **Usar datos de ejemplo**, revisa KPIs y gráficos, y pulsa **Generar resumen y audio**.

## Formato del CSV
Columnas obligatorias: `order_id, date, category, amount, is_purchase`; mínimo 100 filas; máximo 10 MB.
- `date`: AAAA-MM-DD. `amount`: numérico. `is_purchase`: 1/0, true/false, yes/no, sí/no.

**Regla de valores faltantes**
- Fila con `date`, `amount` o `is_purchase` vacío → se descarta (la app indica cuántas).
- `category` vacía → "Sin categoría".
- Valor presente pero inválido (p. ej. `amount=abc`) → se rechaza el archivo con mensaje claro.
- En la serie temporal, los días sin compras se muestran con ventas = 0.

## KPIs
| KPI | Fórmula |
|---|---|
| total_sales | Σ amount con is_purchase = True |
| total_transactions | número de filas válidas |
| purchases_count | filas con is_purchase = True |
| avg_amount_per_transaction | Σ amount (todas) / total_transactions |
| avg_amount_per_purchase | total_sales / purchases_count |
| conversion_rate | purchases_count / total_transactions |
| ticket_mean | total_sales / total_transactions |

Métrica categórica: ventas y compras por categoría (`category_breakdown`).

## Variables de entorno
| Variable | Uso |
|---|---|
| `GEMINI_API_KEY` | Clave de Gemini; vacía → resumen SIMULADO |
| `ELEVENLABS_API_KEY` | Clave de ElevenLabs; vacía → audio SIMULADO (tono) |
| `ELEVENLABS_VOICE_ID` | Voz opcional (por defecto una voz premade) |
| `GEMINI_MODEL` | Modelo opcional (por defecto `gemini-2.5-flash`) |
| `MAX_HISTORY` | Resúmenes en historial (por defecto 5) |

## Modo simulado (sin claves o sin cuota)
Deja vacías `GEMINI_API_KEY` y/o `ELEVENLABS_API_KEY` en `.env`. La app muestra un aviso y etiqueta el resultado como **SIMULADA**. Si la API falla (red, timeout, cuota agotada, respuesta no válida) también se usa la simulación automáticamente.

## Privacidad
A Gemini solo se envían estadísticas agregadas (`aggregate_for_gemini`, < 500 caracteres), nunca filas. Los logs no registran claves; el dataset se identifica por un hash.

## Pruebas
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
Incluyen validación de CSV, KPIs, gráficos, clientes de Gemini/ElevenLabs con mocks (sin clave, éxito, timeout, error HTTP, respuesta inválida), historial y la interfaz end-to-end con `streamlit.testing`. Los tests fuerzan las claves a vacío, por lo que nunca llaman a las APIs reales.

## Estructura
```
app.py                  interfaz Streamlit
src/kpis.py             validación y KPIs
src/visuals.py          gráficos
src/gemini_client.py    resumen (Gemini o SIMULADA)
src/eleven_client.py    audio (ElevenLabs o SIMULADA)
src/session.py          historial de sesión
src/prompts/summary_template.txt
data/generate_sample.py datos sintéticos
tests/                  pytest
```
