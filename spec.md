# spec.md

## Resumen
Documento técnico que especifica **qué** hace la aplicación del Desafío 3 (Analista ejecutivo de datos con voz) y **cómo** se comporta. Contiene requisitos funcionales y no funcionales, arquitectura, contratos de entrada/salida, variables de entorno, manejo de errores, estrategia de pruebas y criterios de aceptación. Refleja el código de la versión entregada.

---

## Requisitos funcionales (RF)
**RF-01** — **Carga de archivo**: La interfaz permite subir un CSV (máx. 10 MB) o usar `data/sample_sales.csv`.  
**RF-02** — **Validación de CSV**: Columnas obligatorias **order_id, date, category, quantity, amount, is_purchase** (se ignoran columnas adicionales; se toleran mayúsculas, espacios y BOM de Excel). Se exigen ≥100 filas leídas y ≥100 filas válidas tras la limpieza. Se rechaza el archivo, indicando número de línea y valor, si hay: `order_id` duplicado, `quantity` no entera o < 1, `amount` no numérico o negativo, fecha inexistente o fuera del formato AAAA-MM-DD, `is_purchase` no reconocido.  
**RF-03** — **Calidad de datos**: Las filas con `order_id`, `date`, `quantity`, `amount` o `is_purchase` vacíos se descartan; `category` vacía pasa a "Sin categoría". La interfaz muestra filas leídas, válidas, descartadas y celdas vacías por columna.  
**RF-04** — **Cálculo de KPIs**: Ocho KPIs calculados con Python (ver tabla), cada uno con nombre, valor, fórmula y descripción. Las divisiones entre cero devuelven 0.  
**RF-05** — **Visualizaciones**: (a) evolución de ventas por día (periodos ≤31 días) o por semana (periodos mayores, con las semanas incompletas del periodo marcadas); (b) ventas por categoría con monto y participación. Ambas descargables en PNG.  
**RF-06** — **Agregación para Gemini**: Texto con periodo, filas analizadas, los 8 KPIs, ventas/participación/unidades por categoría y ventas por mes; nunca filas individuales.  
**RF-07** — **Generación de resumen**: Gemini devuelve JSON (`resumen`, `hallazgos`, `recomendaciones`). Los datos calculados se muestran aparte, nunca redactados por el modelo. Si el texto contiene cifras que no coinciden (admitiendo redondeo) con las estadísticas, se muestra una advertencia.  
**RF-08** — **Síntesis de voz**: El resumen, hallazgos y recomendaciones se envían a ElevenLabs (máx. 2 500 caracteres) y el audio se reproduce en la interfaz.  
**RF-09** — **Historial de sesión**: Se guardan en memoria los últimos `MAX_HISTORY` (5 por defecto) resúmenes, indicando si el texto o el audio fueron simulados.  
**RF-10** — **Fallbacks**: Sin clave o ante un fallo de la API se muestra el motivo y una respuesta **SIMULADA** claramente marcada (texto de demostración / tono WAV que no es voz).  
**RF-11** — **Exportar informe**: Descarga del resumen en `.txt` con los datos calculados y la interpretación en secciones separadas.  
**RF-12** — **Coherencia**: Si se carga otro archivo, no se muestra el resumen generado con el archivo anterior.

### KPIs implementados (`src/kpis.py`, `KPI_DEFINITIONS`)
| Clave | Nombre | Fórmula |
|---|---|---|
| `total_sales` | Ventas totales | Σ amount con is_purchase = True |
| `total_transactions` | Transacciones | número de filas válidas |
| `purchases_count` | Compras | filas con is_purchase = True |
| `conversion_rate` | Tasa de conversión | purchases_count / total_transactions |
| `avg_amount_per_purchase` | Ticket medio | total_sales / purchases_count |
| `units_sold` | Unidades vendidas | Σ quantity con is_purchase = True |
| `avg_units_per_purchase` | Unidades por compra | units_sold / purchases_count |
| `avg_unit_price` | Precio medio por unidad | total_sales / units_sold |

Métrica categórica: `category_breakdown` (ventas, compras, unidades y participación por categoría).

---

## Requisitos no funcionales (RNF)
**RNF-01** — **Seguridad de credenciales**: Las claves se leen desde `.env` (excluido por `.gitignore`); `.env.example` sin valores. Los mensajes y logs nunca incluyen claves ni el texto de las excepciones de las APIs.  
**RNF-02** — **Privacidad**: Solo estadísticas agregadas a Gemini; aviso visible en la interfaz. El dataset se identifica en logs con un hash.  
**RNF-03** — **Robustez**: Los clientes nunca lanzan excepciones a la interfaz; un CSV inválido muestra un error y detiene el flujo sin cerrar la app.  
**RNF-04** — **Portabilidad**: Python 3.11+ (probado con 3.14.8 en Windows); dependencias en `requirements.txt`.  
**RNF-05** — **Testabilidad**: Pruebas automatizadas con mocks para Gemini y ElevenLabs; los tests fuerzan las claves a vacío.  
**RNF-06** — **Rendimiento**: Procesamiento de CSV de 100–10 000 filas en < 5 s en hardware de desarrollo típico (estimado, no medido formalmente).  
**RNF-07** — **Accesibilidad**: Reproductor de audio nativo; gráficos de un solo color con etiquetas de valor; el modo simulado se indica con texto, no solo con color.

---

## Arquitectura y flujo de datos
**Componentes**
- **Interfaz (`app.py`, Streamlit)**: barra lateral (carga, estado de claves, aviso de privacidad), calidad de datos, KPIs, gráficos, resumen, recomendaciones, audio e historial.  
- **Validación y KPIs (`src/kpis.py`)**: `validate_csv`, `compute_kpis`, `format_kpi`, `category_breakdown`, `monthly_sales`, `aggregate_for_gemini`.  
- **Visualizaciones (`src/visuals.py`)**: matplotlib (`timeseries_figure`, `category_figure`, `fig_to_png`).  
- **Integración Gemini (`src/gemini_client.py`)**: SDK oficial `google-genai`, plantilla `src/prompts/summary_template.txt`, salida JSON con esquema, clasificación de errores y verificación de cifras.  
- **Integración ElevenLabs (`src/eleven_client.py`)**: API REST oficial `POST /v1/text-to-speech/{voice_id}` con `requests`; fallback a tono WAV.  
- **Historial (`src/session.py`)**: `SessionHistory` en memoria (deque).  
- **Datos de ejemplo (`data/generate_sample.py`)**: 200 pedidos sintéticos con semilla fija.

**Flujo de datos**
1. Usuario sube CSV → `validate_csv` → DataFrame tipado + `attrs["quality"]`.  
2. `compute_kpis` y `visuals` → KPIs y gráficos en la interfaz.  
3. `aggregate_for_gemini(df)` → texto agregado → `generate_summary` → resumen, hallazgos, recomendaciones.  
4. `speech_text` → `synthesize_audio` → audio reproducible.  
5. `format_report` → historial y exportación `.txt`.

---

## Contratos de entrada/salida (I/O)
### `validate_csv(source: str | IO) -> DataFrame`
- **Salida**: columnas `order_id` (str), `date` (datetime), `category` (str), `quantity` (int), `amount` (float), `is_purchase` (bool); `df.attrs["quality"] = {rows_read, rows_valid, dropped_rows, missing}`.  
- **Errores**: `ValueError` con mensaje para el usuario (ver "Manejo de errores").

### `compute_kpis(df) -> Dict[str, float]`
- Las 8 claves de la tabla de KPIs, redondeadas (2 decimales; 4 en `conversion_rate`).

### `aggregate_for_gemini(df) -> str`
- Texto plano de ≈600 caracteres con estadísticas agregadas (≤1 000 verificado en pruebas).

### `generate_summary(aggregated_stats, prompt_template=None, *, api_key=None, client_factory=None) -> Dict`
- **Salida**: `{facts, summary, findings: [str], recommendations: [str], simulated: bool, error: str|None, warning: str|None}`. Nunca lanza excepciones.

### `synthesize_audio(text, *, api_key=None, voice_id=None) -> Dict`
- **Salida**: `{audio: bytes, mime: "audio/mpeg"|"audio/wav", simulated: bool, error: str|None, truncated: bool}`. Nunca lanza excepciones.

---

## Variables de entorno
**Claves (desde `.env`; vacías → modo simulado)**
- `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`.

**Opcionales**
- `GEMINI_MODEL` — por defecto `gemini-3.6-flash`.  
- `ELEVENLABS_VOICE_ID` — por defecto `21m00Tcm4TlvDq8ikWAM`.  
- `MAX_HISTORY` — por defecto 5 (mínimo 1).

---

## Manejo de errores y mensajes al usuario
**Errores de entrada** (prefijo en la UI: "El archivo no cumple los requisitos.")
- Archivo vacío o no legible → "No se pudo leer el archivo. Verifica que sea un CSV válido guardado en UTF-8."  
- Columnas faltantes → "Faltan columnas obligatorias: X. Columnas encontradas: …"  
- Filas insuficientes → "El archivo debe tener al menos 100 filas; encontrado N." / "Tras descartar K fila(s) con valores faltantes quedan N filas válidas…"  
- Tipos/valores → "amount no numérico: 1 fila(s); p. ej. línea 102: 'abc'." (análogo para quantity, date, is_purchase, order_id duplicado, amount negativo).

**Errores de integración** (siempre seguidos de la respuesta SIMULADA)
| Situación | Gemini | ElevenLabs |
|---|---|---|
| Sin clave | Clave no configurada | Clave no configurada |
| Clave inválida | HTTP 400 "API key" / 401 / 403 | HTTP 401 |
| Cuota agotada | HTTP 429 / `RESOURCE_EXHAUSTED` | `detail.status = quota_exceeded` |
| Límite de plan o velocidad | — | HTTP 402 (voz de pago) / HTTP 429 |
| Modelo no disponible | HTTP 404 | — |
| Red / timeout | `httpx.TransportError`, `TimeoutError` | `requests.ConnectionError`, `Timeout` |
| Respuesta inválida | JSON sin las claves esperadas | respuesta no `audio/*` |

**Logs**: tipo de excepción, código HTTP, modelo/voz y hash de las estadísticas; nunca claves.

---

## Estrategia de pruebas
**Unitarias**: validación CSV (vacío, solo encabezado, binario, BOM, separador incorrecto, columnas faltantes, <100 filas, tipos inválidos, fechas inexistentes, duplicados, faltantes), KPIs (valores conocidos, sin compras), formato, desglose por categoría y mes, agregación sin filas, gráficos (títulos, etiquetas, totales).  
**Integración con mocks**: Gemini (éxito, cuota, clave inválida, permiso, modelo, servidor, red, timeout, formato inválido, cifras no verificables, claves no expuestas) y ElevenLabs (éxito, voz, red, 401, cuota, 402, 429, 500, contenido no audio, truncado).  
**Interfaz**: `streamlit.testing.AppTest` sin claves (avisos, KPIs, flujo completo simulado, historial).  
**Manual pendiente**: ejecución con claves reales de Gemini y ElevenLabs.

---

## Criterios de aceptación por funcionalidad
- **Carga y validación**: `data/sample_sales.csv` → "Archivo válido: 200 filas analizadas" y KPIs.  
- **KPIs**: coinciden con los cálculos independientes de `tests/test_kpis.py`.  
- **Visualizaciones**: ambos gráficos se generan y descargan.  
- **Resumen**: Gemini (o simulación) devuelve resumen, hallazgos y recomendaciones separados de los datos calculados.  
- **Audio**: ElevenLabs (o tono simulado identificado) reproducible.  
- **Seguridad**: `.env` ignorado; `.env.example` presente; sin claves en el repositorio.  
- **Pruebas**: `pytest` pasa completo.

---

## Notas operativas y límites
- **No enviar filas** a Gemini.  
- **Cuotas**: sin clave o sin créditos, la app sigue funcionando en modo simulado.  
- **Tamaño de archivo**: máximo 10 MB.  
- **Prompt**: `src/prompts/summary_template.txt`.
