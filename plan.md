# plan.md

## Resumen ejecutivo
> Fase 1. Definir: Seleccionar desafío y redactar intent.md antes de generar código.  
> Fase 5. Integrar: Conectar Gemini, probar salida textual y después integrar ElevenLabs.

Este plan divide el trabajo en fases claras, tareas pequeñas, responsables y evidencia de finalización. Incluye al menos tres ciclos de desarrollo (prompt → código → ejecución → error/observación → corrección), criterios de entrega y planes alternativos ante fallos de cuota o ausencia de claves.

---

## Fases y entregables (alto nivel)
1. **Preparación (Fase 1)**  
   - Entregables: `intent.md` finalizado; decisión del desafío (Desafío 3 confirmado).  
   - Tiempo estimado: 0.5 días.  
   - Responsable: *Anthony*.

2. **Diseño (Fase 2)**  
   - Entregables: `spec.md` con requisitos funcionales y no funcionales, arquitectura y contratos I/O.  
   - Tiempo estimado: 1 día.  
   - Responsable: *Anthony*.

3. **Planificación detallada (Fase 3)**  
   - Entregables: `plan.md` (este documento) con tareas, responsables y riesgos; backlog inicial.  
   - Tiempo estimado: 0.5 días.  
   - Responsable: *Anthony*.

4. **Construcción (Fase 4)**  
   - Entregables: esqueleto del repo, módulos de validación y cálculo de KPIs, generación de visualizaciones básicas.  
   - Tiempo estimado: 2 días.  
   - Responsable: *Anthony*.

5. **Integración (Fase 5)**  
   - Entregables: integración con Gemini (texto) y ElevenLabs (TTS) o mocks; control de reproducción de audio.  
   - Tiempo estimado: 1.5 días.  
   - Responsable: *Anthony*.

6. **Verificación y pruebas (Fase 6)**  
   - Entregables: pruebas unitarias, pruebas de error (sin clave, cuota agotada, CSV inválido), evidencia (capturas/video).  
   - Tiempo estimado: 1 día.  
   - Responsable: *Anthony*.

7. **Comunicación y entrega (Fase 7)**  
   - Entregables: README, reflexión crítica (250–400 palabras), paquete final (ZIP o repo).  
   - Tiempo estimado: 0.5 días.  
   - Responsable: *Anthony*.

---

## Tareas desglosadas (con responsables y evidencia)
- **T1**: Crear repositorio y estructura inicial (`intent.md`, `spec.md`, `plan.md`, `.gitignore`, `.env.example`).  
  - Responsable: *Anthony*.  
  - Evidencia: PR inicial o ZIP con estructura.

- **T2**: Generar `data/sample_sales.csv` sintético (≥100 filas).  
  - Responsable: *Anthony*.  
  - Evidencia: `data/sample_sales.csv` en repo.

- **T3**: Implementar validación CSV (`src/kpis.validate_csv`).  
  - Responsable: *Anthony*.  
  - Evidencia: test unitario que falla/vence.

- **T4**: Implementar cálculo de KPIs (`src/kpis.compute_kpis`) y función de agregación para Gemini.  
  - Responsable: *Anthony*.  
  - Evidencia: test que valida al menos un KPI.

- **T5**: Crear visualizaciones (serie temporal y distribución por categoría) en `src/visuals.py`.  
  - Responsable: *Anthony*.  
  - Evidencia: imágenes generadas o componentes en la interfaz.

- **T6**: Esqueleto de interfaz (Streamlit recomendado) con carga de CSV, vista de KPIs y gráficos.  
  - Responsable: *Anthony*.  
  - Evidencia: `app.py` ejecutable localmente.

- **T7**: Integración Gemini (cliente, prompt template, manejo de errores).  
  - Responsable: *Anthony*.  
  - Evidencia: prueba de generación textual (real o mock).

- **T8**: Integración ElevenLabs (envío de texto y reproducción de audio; fallback simulado).  
  - Responsable: *Anthony*.  
  - Evidencia: audio reproducible o simulación marcada.

- **T9**: Pruebas de error y seguridad (sin claves, cuota agotada, CSV inválido).  
  - Responsable: *Anthony*.  
  - Evidencia: tests y capturas/video.

- **T10**: Documentación final y reflexión crítica.  
  - Responsable: *Anthony*.  
  - Evidencia: `README.md`, reflexión en repo.

- **T11**: Revisión integral (calidad de datos, `quantity`, KPI, errores de API, interfaz, documentación y limpieza).  
  - Responsable: *Anthony*.  
  - Evidencia: Iteración 5 y `evidencia/pytest_output.txt`.

### Estado de las tareas
| Tarea | Estado | Comprobación |
|---|---|---|
| T1 Estructura | Completada | archivos en el repositorio |
| T2 Datos de ejemplo | Completada | `test_sample_data.py` |
| T3 Validación CSV | Completada | `test_kpis.py` (validación y calidad) |
| T4 KPIs y agregación | Completada | `test_kpis.py` (KPIs) |
| T5 Visualizaciones | Completada | `test_visuals.py`, `evidencia/*.png` |
| T6 Interfaz | Completada | `test_app.py`, arranque real de Streamlit |
| T7 Gemini | Completada | `test_gemini_client.py`; prueba real con clave válida y `gemini-4-hydrogen`: respuesta `simulado: False`; en la app, 503 y 504 del servicio manejados con mensaje y respuesta SIMULADA |
| T8 ElevenLabs | Completada | `test_eleven_client.py`; prueba real con clave válida: audio `audio/mpeg` generado (37 659 bytes); reproducción en la app verificada |
| T9 Pruebas de error y seguridad | Completada | pruebas de errores, escaneo de claves |
| T10 Documentación y reflexión | Parcial: falta revisión personal de `REFLEXION.md` y video | — |
| T11 Revisión integral | Completada | Iteración 5 |

---

## Ciclos de desarrollo (mínimo 3 ciclos obligatorios)
Cada ciclo debe registrarse en `plan.md` con: problema, prompt usado con el asistente, cambio aplicado y resultado.

### Ciclo 1 — Falso rechazo por celdas vacías en `is_purchase` (Iteraciones 2 → 3)
- **Problema**: La prueba `test_missing_values_rule` falló: `is_purchase inválido: valores no reconocidos (1.0)`. Con una celda vacía, pandas leía la columna como decimal y el valor `1` llegaba como `"1.0"`.
- **Prompt**: Corrección propia tras el fallo de la Iteración 2 (ver registro de iteraciones).
- **Cambio aplicado**: `_TRUE`/`_FALSE` aceptan `1.0`/`0.0` y el CSV se lee con `dtype=str`.
- **Resultado**: 43 pruebas aprobadas en ese momento; el caso borde queda cubierto por prueba.

### Ciclo 2 — Revisión de calidad de datos y KPI ambiguos (Iteración 5)
- **Problema**: Faltaba la columna `quantity`; `order_id` vacío o duplicado no se detectaba; un CSV de Excel con BOM se rechazaba; el mínimo de 100 filas se comprobaba antes de descartar faltantes; `ticket_mean` y `avg_amount_per_transaction` eran ambiguos.
- **Prompt**: "Revisión, corrección y optimización — Laboratorio 4, Reto 3" (revisar y corregir sin rehacer el proyecto).
- **Cambio aplicado**: Validación de `quantity`, `order_id`, BOM y umbral de filas válidas tras la limpieza; los KPI se definen en un único `KPI_DEFINITIONS` y se retiran los dos ambiguos.
- **Resultado**: 1.ª ejecución con 1 fallo: `test_sample_shows_kpis_and_charts` esperaba un orden visual que `AppTest` no garantiza; la prueba se corrigió para comparar el conjunto. Ejecución final: 89 aprobadas (`evidencia/pytest_output.txt`).

### Ciclo 3 — Errores de API poco claros y redacción de cifras por el modelo (Iteración 5)
- **Problema**: Cuota, clave inválida, modelo y red devolvían el mismo mensaje; `gemini-2.5-flash` ya no se ofrecía a proyectos nuevos; Gemini redactaba también los cálculos verificables.
- **Prompt**: Mismo prompt de revisión de la Iteración 5.
- **Cambio aplicado**: Mensajes específicos por tipo de error en Gemini y ElevenLabs; salida JSON de Gemini (resumen, hallazgos, recomendaciones) separada de los datos calculados; verificación de cifras no presentes en las estadísticas.
- **Resultado**: Llamadas reales con clave ficticia: Gemini → 400 (clave inválida) y ElevenLabs → 401, ambas detectadas. Pendiente: prueba con claves válidas.

---

## Criterios de finalización por tarea
- Código con pruebas que pasan localmente (`pytest`).  
- `.env.example` presente; claves reales no incluidas; `.gitignore` configurado.  
- Capturas o video (máx. 2 minutos) que muestren: carga CSV, KPIs, gráficos, texto generado y reproducción de audio.  
- Registro de ≥3 iteraciones en `plan.md` (este archivo actualizado con entradas de ciclo).  
- README con pasos reproducibles para ejecutar localmente y cómo simular falta de claves.

---

## Riesgos, dependencias y plan alternativo
- **Riesgo**: Agotamiento de cuota en ElevenLabs o Gemini.  
  - **Mitigación**: Implementar respuestas simuladas claramente marcadas; incluir pruebas que usen mocks.  
- **Riesgo**: Usuario sube CSV con datos sensibles.  
  - **Mitigación**: Advertencia en UI; no enviar filas a Gemini; enviar solo estadísticas agregadas.  
- **Dependencias**: Acceso a Internet para APIs; versiones de pandas/numpy; cuenta ElevenLabs con TTS disponible.  
- **Plan alternativo**: Si no hay acceso a APIs, entregar demo con mocks y evidencia de integración local previa (logs, request samples sin claves).

---

## Checklist de entrega
- [x] `intent.md` (completo)  
- [x] `spec.md` (completo)  
- [x] `plan.md` (este archivo, con ciclos registrados)  
- [x] Código en `src/`, `app.py` y `data/sample_sales.csv`  
- [x] `requirements.txt`, `.env.example`, `.gitignore`  
- [x] Tests en `tests/` y resultados de `pytest` (captura)  
- [x] Capturas demostrativas con claves reales: `evidencia/PruebaDesafio01.png` (resumen generado por Gemini), `evidencia/PruebaDesafio02.png` (reproductor y historial), `evidencia/AudioDePrueba.mp3` (audio del resumen) y `evidencia/PruebaDesafio03.png` (error manejado: clave no configurada y respuesta SIMULADA)
- [ ] Reflexión crítica (250–400 palabras) — borrador en `REFLEXION.md`, pendiente de revisión personal

---

## Registro de iteraciones

### Iteración 0 — Verificación del entorno (Paso A) — 2026-10-29
- **Problema**: Confirmar versión de Python, dependencias y estado inicial de tests.
- **Prompt**: "Paso A: Verificación del entorno (python --version, pip install -r requirements.txt, pytest -q)".
- **Archivos modificados**: ninguno.
- **Resultado**: Python 3.14.8 OK. `requirements.txt` inexistente. `pytest` no instalado (`No module named pytest`). Carpeta solo contiene intent/spec/plan.
- **Estado**: resuelto (ver Iteración 1).

### Iteración 1 — Estructura inicial y dependencias (T1) — 2026-10-29
- **Problema**: Faltaba estructura del repo, requirements y pytest.
- **Prompt**: "T1: crear .gitignore, .env.example, requirements.txt, src/, tests/, data/ y .venv propio; instalar dependencias".
- **Archivos modificados**: creados `.gitignore`, `.env.example`, `requirements.txt`, `src/__init__.py`, `tests/__init__.py`, carpetas `data/`, `src/prompts/`.
- **Resultado**: pip install exit 0 (pandas 3.1.0, streamlit 1.66.1, google-genai 2.34.0, elevenlabs 2.75.0, pytest 9.2.0). `pytest -q` → "no tests ran" (exit 5, esperado). `.env` no existe; `.env.example` sin valores.
- **Estado**: resuelto.

### Iteración 2 — Implementación T2–T9 con mocks — 2026-10-29
- **Problema**: Implementar datos de ejemplo, validación, KPIs, gráficos, clientes Gemini/ElevenLabs con fallback SIMULADA, historial e interfaz.
- **Prompt**: "Sigue, avanza sin consultar pero haz todas las pruebas necesarias para que no haya errores".
- **Archivos modificados**: creados `data/__init__.py`, `data/generate_sample.py`, `data/sample_sales.csv`, `pytest.ini`, `src/kpis.py`, `src/visuals.py`, `src/gemini_client.py`, `src/eleven_client.py`, `src/session.py`, `src/prompts/summary_template.txt`, `app.py`, `tests/conftest.py`, `tests/test_sample_data.py`, `tests/test_kpis.py`, `tests/test_visuals.py`, `tests/test_gemini_client.py`, `tests/test_eleven_client.py`, `tests/test_session.py`, `tests/test_app.py`; `.env.example` (+`GEMINI_MODEL`).
- **Resultado**: `pytest -q` → `1 failed, 42 passed`. Falla `test_missing_values_rule`: `ValueError: is_purchase inválido: valores no reconocidos (1.0)`.
- **Estado**: resuelto en Iteración 3.

### Iteración 3 — is_purchase con celdas vacías se leía como float — 2026-10-29
- **Problema**: Si `is_purchase` tiene una celda vacía, pandas infiere `float64` y el valor `1` llega como `"1.0"`, que no estaba en los valores aceptados → se rechazaba un CSV válido.
- **Prompt**: (corrección propia tras el fallo de la Iteración 2).
- **Archivos modificados** (`src/kpis.py`):
  ```diff
  -_TRUE = {"1", "true", "yes", "y", "si", "sí", "t"}
  -_FALSE = {"0", "false", "no", "n", "f"}
  +_TRUE = {"1", "1.0", "true", "yes", "y", "si", "sí", "t"}
  +_FALSE = {"0", "0.0", "false", "no", "n", "f"}
  ...
  -        df = pd.read_csv(source)
  +        # Se lee todo como texto para que una celda vacía no convierta 1 en "1.0".
  +        df = pd.read_csv(source, dtype=str)
  ```
- **Resultado**: `pytest -q` → `43 passed in 6.31s`. `pytest tests/test_kpis.py::test_validate_csv_and_compute_kpis -v` → PASSED. Arranque real `streamlit run app.py` → `/_stcore/health` 200. Escaneo de claves: sin claves reales (solo `"test-key"` ficticio en mocks). `.env` no existe.
- **KPIs de `data/sample_sales.csv`**: total_sales 27393.53; total_transactions 200; purchases_count 118; conversion_rate 0.59; avg_amount_per_purchase 232.15; avg_amount_per_transaction 250.75; ticket_mean 136.97.
- **Estado**: resuelto.

### Iteración 4 — Evidencia, reflexión y repositorio — 2026-10-29
- **Problema**: Completar entregables: evidencia, reflexión, README y repositorio git sin secretos.
- **Prompt**: "continua con todo".
- **Archivos modificados**: creados `README.md`, `REFLEXION.md` (borrador), `evidencia/` (`serie_temporal.png`, `ventas_categoria.png`, `resumen_simulado.txt`, `audio_simulado.wav`, `pytest_output.txt`); checklist de entrega actualizado.
- **Resultado**: `pytest -v` → 43 passed (guardado en `evidencia/pytest_output.txt`). Gráficos revisados visualmente. Resumen simulado contiene las secciones Cálculos verificables / Interpretación / Recomendaciones. Verificación previa al commit: `.env` ausente, sin claves reales, `.venv/` ignorado.
- **Estado**: resuelto.

### Iteración 5 — Revisión, corrección y optimización (T11) — 2026-11-17
- **Problema**: Revisión senior del proyecto. Hallazgos: faltaba la columna `quantity`; no se detectaban `order_id` vacíos o duplicados; un CSV de Excel con BOM se rechazaba; el mínimo de 100 filas se comprobaba antes de descartar faltantes; `ticket_mean` y `avg_amount_per_transaction` eran ambiguos (el segundo promediaba montos de transacciones sin compra); `gemini-2.5-flash` ya no se ofrece a proyectos nuevos; los errores de API no distinguían cuota, clave inválida y red; Gemini redactaba los "cálculos verificables"; la interfaz mostraba el resumen del CSV anterior al cargar otro; el paquete `elevenlabs` estaba en `requirements.txt` sin usarse; la serie temporal diaria era muy ruidosa.
- **Prompt**: "Revisión, corrección y optimización — Laboratorio 4, Reto 3" (revisar y corregir el proyecto existente sin rehacerlo).
- **Archivos modificados**: `data/generate_sample.py` y `data/sample_sales.csv` (+`quantity`), `src/kpis.py`, `src/visuals.py`, `src/gemini_client.py`, `src/prompts/summary_template.txt`, `src/eleven_client.py`, `app.py`, todos los `tests/` salvo `test_session.py`, `requirements.txt`, `.env.example`, `.gitignore`, `intent.md`, `spec.md`, `plan.md`, `README.md`, `evidencia/`.
- **Cambios**: informe de calidad de datos y mensajes con número de línea; 8 KPIs definidos en un único `KPI_DEFINITIONS` (se retiran `ticket_mean` y `avg_amount_per_transaction`; se añaden `units_sold`, `avg_units_per_purchase`, `avg_unit_price`); estadísticas agregadas con periodo, categorías y meses; salida JSON de Gemini (resumen, hallazgos, recomendaciones) separada de los datos calculados y verificación de cifras; mensajes específicos de cuota, clave, modelo y red en ambos clientes; interfaz reorganizada.
- **Resultado**: 1.ª ejecución `1 failed, 88 passed`: `test_sample_shows_kpis_and_charts` esperaba el orden visual de los KPI, pero `AppTest` recorre la cuadrícula por columnas; se corrigió la prueba para comparar el conjunto. Ejecución final registrada en `evidencia/pytest_output.txt`. Llamadas reales con clave ficticia: Gemini → `ClientError 400` → mensaje de clave inválida; ElevenLabs → HTTP 401 → mensaje de clave inválida. `streamlit run app.py` → `/_stcore/health` = ok. Instalación desde cero en un entorno virtual nuevo con `requirements.txt` y `pytest` completo.
- **KPIs de `data/sample_sales.csv`**: ventas totales 22,677.71; transacciones 200; compras 119; conversión 59.5%; ticket medio 190.57; unidades vendidas 376; unidades por compra 3.16; precio medio por unidad 60.31.
- **Estado**: resuelto, salvo la prueba con claves reales (pendiente).

### Iteración 6 — Verificación con claves reales (T7, T8) — 2026-11-18
- **Problema**: Las pruebas automatizadas usan mocks. Hacía falta comprobar la integración real con claves válidas.
- **Prompt**: Pruebas manuales en el equipo local: `prueba_elevenlabs.py` y `prueba_gemini.py` (scripts temporales, no versionados).
- **Resultados**:
  - ElevenLabs: audio `audio/mpeg` de 37 659 bytes, `simulado: False`.
  - Gemini: dos intentos devolvieron `ServerError 503`; en la app, una solicitud devolvió 504 Gateway Timeout tras ~60 s. Tras cambiar `GEMINI_MODEL` a `gemini-4-hydrogen` y repetir la prueba, la respuesta fue `simulado: False` sin error.
- **Cambio aplicado**: `GEMINI_MODEL` en el `.env` local. No se cambió `DEFAULT_MODEL` del código.
- **Resultado**: T7 y T8 verificadas con claves reales. Pendiente: capturas o video de la app.
- **Estado**: resuelto para las integraciones; pendiente la evidencia visual.

### Pendientes
- Revisar y personalizar `REFLEXION.md` (250–400 palabras).
- Revisar y personalizar `REFLEXION.md`.
- Subir el repositorio a un remoto (GitHub) si se entrega así.
