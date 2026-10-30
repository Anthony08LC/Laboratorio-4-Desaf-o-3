# Reflexión crítica

> **BORRADOR** redactado a partir del registro de iteraciones de `plan.md`. Revísalo y adáptalo con tu experiencia personal antes de entregarlo.

Trabajar con un asistente de IA bajo un ciclo explícito de *propuesta → aprobación → ejecución → prueba* cambió la forma en que avancé en el proyecto. Escribir primero `intent.md`, `spec.md` y `plan.md` obligó a fijar contratos concretos (nombres de columnas, firmas como `validate_csv` o `generate_summary`, mensajes de error exactos) antes de que existiera una sola línea de código. Esos contratos se convirtieron directamente en pruebas, y las pruebas en el criterio objetivo para decidir si una tarea estaba terminada.

El aprendizaje más claro vino de un fallo real. La primera ejecución completa dio 42 pruebas aprobadas y una fallida: un CSV válido se rechazaba porque, cuando la columna `is_purchase` tenía una celda vacía, pandas la interpretaba como decimal y el valor `1` llegaba como `"1.0"`. El código "parecía" correcto y habría pasado una revisión visual; solo la prueba de la regla de valores faltantes lo descubrió. La corrección fue pequeña (leer el CSV como texto), pero confirmó que los casos borde deben probarse explícitamente y no asumirse.

También comprobé el valor de diseñar para el fallo desde el inicio. Las integraciones con Gemini y ElevenLabs devuelven siempre una respuesta, real o marcada como SIMULADA, y nunca bloquean la interfaz. Gracias a eso pude probar el flujo de extremo a extremo sin claves, sin gastar cuota y sin riesgo de exponer secretos; las pruebas incluso fuerzan las claves a vacío para impedir llamadas reales accidentales.

Como límites, reconozco que la integración real con las APIs aún debe validarse con claves propias, que el nombre del modelo de Gemini puede cambiar con el tiempo y que algunas definiciones de la especificación eran ambiguas (por ejemplo, la diferencia entre `ticket_mean` y `avg_amount_per_purchase`), lo que exigió tomar y documentar decisiones. La lección principal: la IA acelera la escritura de código, pero la calidad la garantizan la especificación, las pruebas y la revisión humana.
