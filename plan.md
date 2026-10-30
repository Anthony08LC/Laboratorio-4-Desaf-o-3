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

---

## Ciclos de desarrollo (mínimo 3 ciclos obligatorios)
Cada ciclo debe registrarse en `plan.md` con: problema, prompt usado con el asistente, cambio aplicado y resultado.

### Ciclo 1 — Validación y KPI básico
- **Problema**: Validación CSV fallando con formatos mixtos en `is_purchase`.  
- **Prompt**: "Implementa `validate_csv` que acepte 0/1, True/False, 'yes'/'no' y convierta `amount` a numérico; devuelve errores amigables."  
- **Cambio aplicado**: Implementación de `to_bool_series` y coerción de `amount`.  
- **Resultado**: Tests de validación pasan; se documenta en `plan.md`.

### Ciclo 2 — Cálculo y test de KPIs
- **Problema**: `total_sales` no coincide con suma esperada en dataset de prueba.  
- **Prompt**: "Revisa `compute_kpis` para asegurar que `total_sales` suma solo compras y redondea a 2 decimales."  
- **Cambio aplicado**: Ajuste de filtrado por `is_purchase == True` y redondeo.  
- **Resultado**: Test unitario que compara suma esperada pasa.

### Ciclo 3 — Integración de Gemini y manejo de ausencia de clave
- **Problema**: Sin clave Gemini, la interfaz debe mostrar fallback simulado y no bloquear la experiencia.  
- **Prompt**: "Implementa wrapper `generate_summary` que use Gemini si hay clave, o devuelva un resumen simulado marcado como 'SIMULADO' si no hay clave o la llamada falla."  
- **Cambio aplicado**: Wrapper con try/except y flag `simulated_response`.  
- **Resultado**: Interfaz muestra texto simulado y permite generar audio simulado; pruebas de error documentadas.

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
- [ ] Capturas/video demostrativo   — parcial: `evidencia/` (gráficos, resumen y audio simulados, salida de pytest); falta video/capturas de la UI con claves reales
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

### Pendientes
- Probar con claves reales de Gemini y ElevenLabs (crear `.env` local) y grabar capturas/video (≤ 2 min).
- Revisar y personalizar `REFLEXION.md`.
- Subir el repositorio a un remoto (GitHub) si se entrega así.
