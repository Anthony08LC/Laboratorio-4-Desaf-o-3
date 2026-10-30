# intent.md

## Título
**Analista ejecutivo de datos con voz — Laboratorio 4**

## Propósito
Construir un prototipo de aplicación que permita a un gerente cargar un archivo CSV de ventas/atención, calcular KPIs verificables, generar visualizaciones y producir un **resumen ejecutivo en texto y audio** usando Gemini (generación de texto) y ElevenLabs (síntesis de voz). El MVP debe ser reproducible localmente y proteger claves y datos sensibles.

## Problema real
Los gerentes necesitan interpretar rápidamente indicadores operativos y recibir recomendaciones accionables sin depender de análisis manual extenso. Actualmente la extracción de KPIs y la redacción de un resumen ejecutivo consumen tiempo y requieren habilidades analíticas que no siempre están disponibles.

## Usuarios objetivo
- **Gerente de producto/operaciones** que requiere resúmenes ejecutivos rápidos.  
- **Analista junior** que necesita validar cálculos y obtener explicaciones interpretables.  
- **Equipo directivo** que prefiere recibir información en audio para revisarla en movilidad.

## Valor esperado
- Reducir el tiempo para obtener un resumen ejecutivo de un dataset a minutos.  
- Entregar KPIs verificables y visualizaciones que respalden las recomendaciones generadas por el modelo.  
- Facilitar consumo por voz para revisiones rápidas.

## Objetivo general
Entregar una aplicación local que valide un CSV, calcule KPIs, genere dos visualizaciones, solicite a Gemini un resumen ejecutivo basado en estadísticas agregadas y reproduzca el resumen con ElevenLabs.

## Objetivos específicos (3)
1. **Validación y cálculo**: Validar estructura del CSV y calcular al menos cuatro KPIs numéricos y una métrica categórica.  
2. **Comunicación**: Generar un resumen ejecutivo claro que distinga cálculos verificables de interpretaciones y recomendaciones.  
3. **Accesibilidad por voz**: Convertir el resumen ejecutivo a audio reproducible y mantener control de reproducción en la interfaz.

## Alcance del MVP
- Soporte para un CSV con ≥100 filas y ≥5 columnas (incluye al menos 2 numéricas y 1 categórica).  
- Cálculo de 4 KPIs (ej.: total ventas, promedio por transacción, tasa de conversión, ticket medio) y 2 visualizaciones (serie temporal y distribución por categoría).  
- Envío a Gemini solo de estadísticas agregadas (no filas completas).  
- Síntesis de voz con ElevenLabs para el resumen ejecutivo.  
- Historial de sesión con al menos 5 interacciones (resúmenes generados).  
- Manejo de errores para archivos inválidos, ausencia de claves y fallos de red (mensajes amigables).

## Historias de usuario

### Historia 1 — Validación y KPIs
**Como** gerente  
**Quiero** subir un CSV y recibir validación de columnas y tipos, más KPIs calculados automáticamente  
**Para** confiar en que los indicadores son correctos antes de pedir un resumen.

**Criterios de aceptación**
- El sistema rechaza archivos con menos de 100 filas o sin las columnas requeridas y muestra un mensaje claro.  
- Se muestran al menos 4 KPIs calculados con sus fórmulas y valores.  
- Existe una prueba automatizada que valida el cálculo de al menos un KPI usando datos de ejemplo.

### Historia 2 — Visualizaciones y contexto
**Como** analista junior  
**Quiero** ver dos visualizaciones (serie temporal y distribución por categoría) junto a los KPIs  
**Para** entender tendencias y segmentaciones antes de leer el resumen.

**Criterios de aceptación**
- Se generan y muestran dos gráficos interactivos o estáticos exportables.  
- Los gráficos se actualizan con el CSV cargado y manejan valores faltantes con una regla documentada.  
- La interfaz permite descargar las imágenes de las visualizaciones.

### Historia 3 — Resumen ejecutivo con voz
**Como** gerente ocupado  
**Quiero** recibir un resumen ejecutivo en texto y audio que distinga hechos de interpretaciones  
**Para** tomar decisiones rápidas y saber qué recomendaciones son verificables.

**Criterios de aceptación**
- El texto del resumen incluye una sección **Cálculos verificables** con los KPIs usados.  
- El texto incluye una sección **Interpretación y recomendaciones** claramente separada.  
- El resumen se convierte a audio y puede reproducirse/pausarse en la interfaz.  
- Si no hay clave de Gemini o ElevenLabs, la app muestra un mensaje y permite reproducir una versión simulada claramente marcada.

## Restricciones y supuestos
- **Restricciones**: No subir datos personales reales; no incluir claves en el repositorio; usar `.env` para credenciales; respetar límites del plan gratuito de ElevenLabs y Gemini.  
- **Supuestos**: El CSV no contiene datos sensibles; el usuario dispone de conexión a Internet para llamadas a APIs; el modelo Gemini puede recibir solo estadísticas agregadas por privacidad.

## Riesgos principales
- Agotamiento de cuota en ElevenLabs o Gemini.  
- Respuestas de Gemini que mezclen hechos con inferencias sin señalización.  
- Errores en la validación de tipos que produzcan KPIs incorrectos.

## Definición de éxito
La solución se considera exitosa si:
- Un CSV de ejemplo (≥100 filas) produce 4 KPIs correctos y 2 visualizaciones reproducibles.  
- Gemini genera un resumen que incluye las secciones **Cálculos verificables** y **Recomendaciones**; ElevenLabs reproduce el audio del resumen.  
- El repositorio contiene `intent.md`, `spec.md`, `plan.md`, `.env.example`, `README.md` y pruebas automatizadas que simulan ausencia de claves y validan al menos una función de negocio.  
- Las claves reales no aparecen en el repositorio y las pruebas de error (archivo inválido, falta de clave, fallo de red) muestran mensajes amigables.

## Métricas de evaluación (cómo se comprobará)
- **Funcionalidad**: ejecución end-to-end con CSV de ejemplo que genera KPIs, gráficos, texto y audio.  
- **Seguridad**: verificación de `.gitignore` y ausencia de claves en el repo.  
- **Pruebas**: existencia de tests unitarios que cubran validación de CSV y cálculo de al menos un KPI.  
- **Documentación**: `spec.md` y `plan.md` coherentes con el MVP y evidencia de ≥3 iteraciones documentadas.

## Notas operativas
- Mantener un archivo `data/sample_sales.csv` con datos sintéticos para pruebas.  
- Registrar en `plan.md` responsables y tiempos; asignar a un integrante la verificación final de que no hay secretos en el repo.  
- En caso de agotamiento de cuota, incluir una ruta de demostración con respuestas simuladas claramente etiquetadas.
