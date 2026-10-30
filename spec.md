# spec.md

## Resumen
Documento técnico que especifica **qué** debe hacer la aplicación del Desafío 3 (Analista ejecutivo de datos con voz) y **cómo** debe comportarse. Contiene requisitos funcionales y no funcionales, arquitectura, contratos de entrada/salida, variables de entorno, manejo de errores, estrategia de pruebas y criterios de aceptación.

---

## Requisitos funcionales (RF)
**RF-01** — **Carga de archivo**: La interfaz permitirá subir un archivo CSV.  
**RF-02** — **Validación de CSV**: Validar columnas obligatorias: **order_id, date, category, amount, is_purchase**; verificar tipos, detectar filas faltantes y exigir ≥100 filas. Mostrar errores amigables.  
**RF-03** — **Cálculo de KPIs**: Calcular al menos cuatro KPIs verificables: **total_sales, total_transactions, purchases_count, avg_amount_per_purchase**; además incluir **conversion_rate** y **ticket_mean**. Mostrar fórmula y valor.  
**RF-04** — **Visualizaciones**: Generar dos visualizaciones: (a) serie temporal de ventas por fecha y (b) distribución por categoría. Permitir descarga de las imágenes.  
**RF-05** — **Agregación para Gemini**: Preparar y enviar solo estadísticas agregadas (KPIs y descriptores) a Gemini; nunca enviar filas individuales.  
**RF-06** — **Generación de resumen**: Solicitar a Gemini un **resumen ejecutivo** que incluya: **Cálculos verificables**, **Interpretación**, y **Recomendaciones**.  
**RF-07** — **Síntesis de voz**: Enviar el texto del resumen a ElevenLabs y reproducir el audio en la interfaz con controles de reproducir/pausar.  
**RF-08** — **Historial de sesión**: Mantener historial local de al menos 5 resúmenes generados durante la sesión.  
**RF-09** — **Fallbacks**: Si falta clave o la API falla, mostrar mensajes claros y ofrecer una **respuesta simulada** marcada como *SIMULADA*.  
**RF-10** — **Exportar informe**: Permitir exportar un resumen ejecutivo en texto (archivo .txt) y descargar las visualizaciones (opcional).

---

## Requisitos no funcionales (RNF)
**RNF-01** — **Seguridad de credenciales**: Las claves deben leerse desde `.env` y **no** almacenarse en el repositorio. Incluir `.env.example`.  
**RNF-02** — **Privacidad**: No enviar datos fila a fila a Gemini; solo estadísticas agregadas. Mostrar aviso al usuario.  
**RNF-03** — **Robustez**: Manejar fallos de red, ausencia de clave y respuestas inválidas de las APIs con mensajes amigables.  
**RNF-04** — **Portabilidad**: Ejecutable localmente en Python 3.11+; dependencias en `requirements.txt`.  
**RNF-05** — **Testabilidad**: Tener tests automatizados que cubran validación de CSV, cálculo de KPIs y simulación de fallos de API (mocks).  
**RNF-06** — **Rendimiento**: Procesamiento de CSV de 100–10,000 filas en < 5s en hardware de desarrollo típico (estimado).  
**RNF-07** — **Accesibilidad**: Controles de audio accesibles y textos legibles; colores con contraste suficiente.

---

## Arquitectura y flujo de datos
**Componentes principales**
- **Interfaz (Streamlit / app.py)**: carga de CSV, visualización de KPIs y gráficos, botones para generar resumen y reproducir audio, historial de sesión.  
- **Módulo de validación y KPIs (`src/kpis.py`)**: validación de columnas/tipos, limpieza, cálculo de KPIs y preparación de estadísticas agregadas.  
- **Módulo de visualizaciones (`src/visuals.py`)**: generación de gráficos (matplotlib/plotly) y exportación.  
- **Integración Gemini (`src/gemini_client.py`)**: plantilla de prompt, envío de estadísticas agregadas, manejo de errores y timeouts.  
- **Integración ElevenLabs (`src/eleven_client.py`)**: envío de texto a TTS, recepción de audio (stream o archivo temporal) y control de reproducción.  
- **Persistencia de sesión (`src/session.py`)**: historial en memoria (o archivo temporal) con últimos 5 resúmenes.  
- **Tests (`tests/`)**: unitarios y de integración con mocks para APIs.

**Flujo de datos**
1. Usuario sube CSV → Interfaz.  
2. Interfaz llama a `kpis.validate_csv` → DataFrame validado.  
3. `kpis.compute_kpis` calcula KPIs → resultados mostrados en UI.  
4. `visuals` genera gráficos a partir del DataFrame → mostrados y disponibles para descarga.  
5. `kpis.aggregate_for_gemini` prepara texto con estadísticas agregadas → enviado a `gemini_client`.  
6. Gemini devuelve resumen → mostrado en UI.  
7. Texto del resumen enviado a `eleven_client` → audio reproducible.  
8. Historial de resumenes guardado en `session`.

---

## Contratos de entrada/salida (I/O)
### Carga CSV (UI → backend)
- **Entrada**: archivo CSV multipart.  
- **Salida**: JSON interno / DataFrame; en UI: tabla de validación y mensajes.

### `validate_csv(path: str) -> DataFrame`
- **Entrada**: ruta a CSV o buffer.  
- **Salida**: DataFrame con columnas normalizadas (`date` datetime, `amount` float, `is_purchase` boolean).  
- **Errores**: `ValueError` con mensajes: *Columnas faltantes*, *menos de 100 filas*, *amount no numérico*, *is_purchase inválido*.

### `compute_kpis(df: DataFrame) -> Dict[str, float]`
- **Entrada**: DataFrame validado.  
- **Salida**: Diccionario con KPIs: `total_sales`, `total_transactions`, `purchases_count`, `avg_amount_per_transaction`, `avg_amount_per_purchase`, `conversion_rate`, `ticket_mean`.

### `aggregate_for_gemini(kpis: Dict) -> str`
- **Entrada**: KPIs.  
- **Salida**: Texto plano con estadísticas agregadas (máx. 300–500 caracteres recomendado).

### `generate_summary(aggregated_stats: str, prompt_template: str) -> Dict`
- **Entrada**: texto de estadísticas y plantilla de prompt.  
- **Salida**: `{ "text": "...", "simulated": False }` o `{ "text": "...", "simulated": True }` en fallback.  
- **Errores**: devolver objeto con `simulated: True` y mensaje de error en logs.

### `synthesize_audio(text: str) -> bytes or url`
- **Entrada**: texto del resumen.  
- **Salida**: bytes de audio o URL/stream temporal para reproducción.  
- **Errores**: fallback a audio simulado (tono TTS local o mensaje hablado por síntesis simple).

---

## Variables de entorno (obligatorias y opcionales)
**Obligatorias (leer desde `.env`)**
- `GEMINI_API_KEY` — clave para Gemini (si no está, usar modo simulado).  
- `ELEVENLABS_API_KEY` — clave para ElevenLabs (si no está, usar modo simulado).

**Opcionales**
- `ELEVENLABS_VOICE_ID` — id de la voz a usar; si no, usar voz por defecto del plan Free.  
- `APP_ENV` — `development` | `production`.  
- `MAX_HISTORY` — número de resúmenes a mantener en sesión (por defecto 5).

**Archivos**
- `.env.example` con variables sin valores reales.  
- `.gitignore` debe incluir `.env` y archivos temporales de audio.

---

## Manejo de errores y mensajes al usuario
**Errores de entrada**
- **Archivo no legible** → "No se pudo leer el archivo. Verifica que sea un CSV válido."  
- **Columnas faltantes** → "Faltan columnas obligatorias: X, Y. Revisa el formato del CSV."  
- **Filas insuficientes** → "El archivo debe tener al menos 100 filas; encontrado N."

**Errores de integración**
- **Falta de clave (Gemini/ElevenLabs)** → Mostrar banner: "Clave de [Gemini/ElevenLabs] no configurada. Usando respuesta simulada marcada como SIMULADA."  
- **Timeout o error API** → "Error al comunicarse con [servicio]. Intenta de nuevo más tarde. Mostrando respuesta simulada."  
- **Respuesta inesperada de Gemini** → Registrar en logs y mostrar: "La respuesta del modelo no cumple el formato esperado; revise los logs."

**Logs y trazabilidad**
- Registrar en archivo local (o consola) las solicitudes a Gemini y ElevenLabs **sin** incluir claves ni datos sensibles. Guardar muestras de prompts y respuestas (hash de dataset si se desea trazabilidad).

---

## Estrategia de pruebas
**Unit tests**
- Validación CSV: columnas faltantes, tipos incorrectos, filas insuficientes.  
- Cálculo de KPIs: casos con compras y sin compras; verificación de sumas y promedios.  
- `aggregate_for_gemini`: formato y contenido mínimo.

**Integration tests (con mocks)**
- Simular respuestas exitosas de Gemini y ElevenLabs.  
- Simular fallos: ausencia de clave, timeout, respuesta inválida.  
- Verificar que la UI muestra fallback simulado y no bloquea.

**Manual tests**
- Carga de `data/sample_sales.csv` (≥100 filas) y verificación end-to-end: KPIs, gráficos, texto y audio.  
- Prueba de descarga de gráficos y exportación de resumen en texto.  
- Captura de pantalla o video corto mostrando ruta feliz y un fallo simulado.

**Cobertura mínima**
- Al menos una prueba automatizada que valide el cálculo de un KPI y una prueba que simule ausencia de clave.

---

## Criterios de aceptación por funcionalidad
- **Carga y validación**: Al subir `data/sample_sales.csv`, la app muestra validación exitosa y KPIs calculados.  
- **KPIs**: Los 4 KPIs principales están presentes y coinciden con cálculos locales verificables.  
- **Visualizaciones**: Ambos gráficos se generan y pueden descargarse.  
- **Resumen**: Gemini (o simulación) devuelve un texto que incluye **Cálculos verificables** y **Recomendaciones**.  
- **Audio**: ElevenLabs (o simulación) produce audio reproducible con controles.  
- **Seguridad**: `.env` no está en el repo; `.env.example` presente.  
- **Pruebas**: `pytest` ejecuta y pasa las pruebas unitarias y las pruebas de error con mocks.

---

## Notas operativas y límites
- **No enviar filas**: por privacidad, nunca enviar filas individuales a Gemini.  
- **Cuotas**: documentar en README cómo activar modo simulado si se agotan créditos.  
- **Tamaño de archivo**: limitar tamaño máximo de CSV en la UI (ej. 10 MB) y mostrar advertencia si excede.  
- **Formato del prompt**: mantener plantilla de prompt en `src/prompts/summary_template.txt` para facilitar revisiones y auditoría.

---
