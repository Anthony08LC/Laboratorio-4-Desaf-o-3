# Analista ejecutivo de datos con voz — Laboratorio 4, Reto 3

Aplicación Streamlit que recibe un CSV de ventas, valida la calidad de los datos, calcula indicadores con Python, muestra gráficos para un gerente, pide a **Gemini** un resumen ejecutivo con hallazgos y recomendaciones y lo convierte en audio con **ElevenLabs**.

Sin claves de API la aplicación sigue funcionando en **modo SIMULADO**, siempre identificado en pantalla.

## Funcionalidades
- Carga de un CSV propio (máx. 10 MB) o de los datos de ejemplo incluidos.
- Validación de columnas, tipos, fechas, identificadores duplicados y valores faltantes, con mensajes que indican la línea del problema.
- Informe de calidad: filas leídas, válidas, descartadas y celdas vacías por columna.
- 8 KPI calculados con Python, con su fórmula y descripción.
- Gráficos de evolución de ventas y ventas por categoría, descargables en PNG.
- Resumen ejecutivo, hallazgos y recomendaciones generados por Gemini a partir de estadísticas agregadas (nunca del CSV completo), separados de los datos calculados.
- Advertencia si el texto del modelo menciona cifras que no están en los datos calculados.
- Audio del resumen con ElevenLabs y reproductor integrado.
- Exportación del informe en `.txt` e historial de los últimos 5 resúmenes de la sesión.

## Tecnologías
Python 3.11+ (probado con 3.14.8 en Windows) · Streamlit · pandas · matplotlib · SDK oficial `google-genai` · API REST oficial de ElevenLabs (`requests`) · python-dotenv · pytest.

## Estructura
```
app.py                          interfaz Streamlit
src/kpis.py                     validación, calidad de datos, KPIs y estadísticas agregadas
src/visuals.py                  gráficos (matplotlib)
src/gemini_client.py            resumen con Gemini (o SIMULADO)
src/eleven_client.py            audio con ElevenLabs (o SIMULADO)
src/session.py                  historial de la sesión
src/prompts/summary_template.txt  prompt enviado a Gemini
data/generate_sample.py         generador de datos sintéticos
data/sample_sales.csv           200 pedidos ficticios
tests/                          pruebas automatizadas (pytest)
evidencia/                      gráficos, resumen y audio simulados, salida de pytest
intent.md · spec.md · plan.md   documentos de ingeniería
REFLEXION.md                    reflexión crítica (borrador)
```

## Instalación
Requisito: Python 3.11 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
En macOS/Linux usa `.venv/bin/python` en lugar de `.\.venv\Scripts\python.exe`.

## Configuración de `.env`
```powershell
copy .env.example .env
```
Edita `.env` y completa las claves. `.env` está en `.gitignore`: **nunca lo subas al repositorio ni lo incluyas en el ZIP de entrega**.

| Variable | Uso |
|---|---|
| `GEMINI_API_KEY` | Clave de Gemini. Vacía → resumen SIMULADO |
| `GEMINI_MODEL` | Opcional. Por defecto `gemini-3.6-flash` |
| `ELEVENLABS_API_KEY` | Clave de ElevenLabs. Vacía → tono SIMULADO |
| `ELEVENLABS_VOICE_ID` | Opcional. Por defecto `21m00Tcm4TlvDq8ikWAM` |
| `MAX_HISTORY` | Opcional. Resúmenes del historial (por defecto 5) |

### Obtener las API Keys
- **Gemini**: entra en [Google AI Studio](https://aistudio.google.com/apikey) con tu cuenta de Google, pulsa *Create API key* y copia el valor en `GEMINI_API_KEY`. Si Google retira el modelo por defecto, indica otro vigente en `GEMINI_MODEL` (lista en la [documentación de modelos](https://ai.google.dev/gemini-api/docs/models)).
- **ElevenLabs**: crea una cuenta en [elevenlabs.io](https://elevenlabs.io), ve a *Settings → API Keys*, crea una clave con permiso de *Text to Speech* y cópiala en `ELEVENLABS_API_KEY`. Si la voz por defecto no está disponible en tu plan (error de plan de pago), copia el *Voice ID* de una voz de tu biblioteca en `ELEVENLABS_VOICE_ID`.

Reinicia Streamlit después de modificar `.env`.

## Ejecución
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Se abre en `http://localhost:8501`.

## Uso
1. En la barra lateral, sube un CSV o marca **Usar datos de ejemplo**. Ahí también se ve si cada clave está configurada.
2. Revisa el mensaje de validación y, si lo hay, el aviso de filas descartadas. *Calidad y vista previa de los datos* muestra las celdas vacías por columna.
3. Consulta los **Indicadores clave** (pasa el cursor para ver la fórmula) y las **Visualizaciones**.
4. Pulsa **Generar resumen ejecutivo y audio**. Se muestran el resumen, los hallazgos, las recomendaciones y el reproductor. Si algo es simulado, aparece la etiqueta **SIMULADO** y el motivo (sin clave, clave inválida, cuota agotada, sin conexión…).
5. Opcional: exporta el informe (`.txt`) o descarga los gráficos.

## Formato del CSV
| Columna | Tipo | Ejemplo |
|---|---|---|
| `order_id` | texto, único | ORD-0001 |
| `date` | fecha AAAA-MM-DD | 2026-01-15 |
| `category` | texto | Hogar |
| `quantity` | entero ≥ 1 | 2 |
| `amount` | número ≥ 0 (monto del pedido) | 59.90 |
| `is_purchase` | 1/0, true/false, yes/no, sí/no | 1 |

Se aceptan columnas adicionales (se ignoran), encabezados con mayúsculas o espacios y archivos UTF-8 con BOM (Excel). Mínimo 100 filas válidas.

**Reglas de calidad de datos**
- Celda vacía en `order_id`, `date`, `quantity`, `amount` o `is_purchase` → la fila se descarta y se informa.
- `category` vacía → "Sin categoría".
- Valor presente pero inválido (texto en `amount`, fecha inexistente, `order_id` duplicado, cantidad 0 o decimal, monto negativo) → se rechaza el archivo indicando la línea.
- En los gráficos, los periodos sin compras se muestran con ventas = 0.

## KPI
| KPI | Fórmula |
|---|---|
| Ventas totales | Σ amount con is_purchase = True |
| Transacciones | número de filas válidas |
| Compras | filas con is_purchase = True |
| Tasa de conversión | Compras / Transacciones |
| Ticket medio | Ventas totales / Compras |
| Unidades vendidas | Σ quantity con is_purchase = True |
| Unidades por compra | Unidades vendidas / Compras |
| Precio medio por unidad | Ventas totales / Unidades vendidas |

Si un denominador es 0, el KPI vale 0. Métrica categórica: ventas, compras, unidades y participación por categoría.

## Privacidad y seguridad
- A Gemini solo se envía el texto de estadísticas agregadas (visible en la app en *Estadísticas agregadas que se envían a Gemini*).
- Las claves se leen de `.env`; los mensajes y logs no las incluyen.
- Los datos de ejemplo son sintéticos. No subas datos personales reales.

## Pruebas
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
Cubren carga y validación del CSV, calidad de datos, KPIs, gráficos, Gemini y ElevenLabs con mocks (éxito, sin clave, clave inválida, cuota, límites, red, formato inválido) y la interfaz con `streamlit.testing`. Los tests vacían las claves, así que nunca llaman a las APIs reales ni consumen cuota.

La integración real con claves válidas se verifica de forma manual: configura `.env`, ejecuta la app con los datos de ejemplo y comprueba que no aparezca la etiqueta SIMULADO.

## Entrega en ZIP
Excluye `.venv/`, `.env`, `__pycache__/` y `.pytest_cache/`. Desde la carpeta del proyecto, con Git:
```powershell
git archive --format=zip -o ..\Laboratorio4_Reto3.zip HEAD
```
