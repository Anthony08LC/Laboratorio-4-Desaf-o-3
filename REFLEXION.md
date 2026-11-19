# Reflexión crítica

Decidimos trabajar con datos sintéticos desde el principio. Un gerente real tiene ventas con información de clientes, así que preferimos generar un CSV ficticio de 200 pedidos y dejar claro en la interfaz que no se deben cargar datos personales. Esa decisión nos obligó a definir el contrato del archivo antes de programar: sin datos reales, había que precisar qué significaba cada columna.

Otra decisión clave fue que Gemini solo recibiera estadísticas agregadas. Enviar filas completas habría sido más sencillo, pero no era necesario para redactar el resumen y aumentaba el riesgo de exponer información. Las cifras las calcula Python y el modelo solo interpreta. Así, al leer el resumen, sabemos qué es un cálculo verificable y qué es una interpretación.

El fallo más importante fue la dependencia del servicio. Durante varios intentos, Gemini respondió con error 503 y después con 504 Gateway Timeout. Al principio sospechamos de la clave o del código, pero el script de prueba funcionó más tarde, cuando el servicio se recuperó. Aprendimos que una aplicación que depende de una API externa necesita un plan alternativo: por eso la app muestra un aviso claro y una respuesta marcada como SIMULADA, en lugar de quedarse en blanco.

En seguridad aprendimos dos cosas. La primera es que las claves van solo en el archivo `.env`, que `.gitignore` excluye, y nunca en el chat, en capturas o en el repositorio. Usamos un `.env.example` sin valores y una prueba automatizada que confirma que el archivo no se versiona. La segunda es que las pruebas automáticas deben correr con mocks, sin claves reales, para no gastar cuota ni exponer secretos.

Como limitación del modelo, nos pareció más relevante que dependa de un servicio externo, con respuestas lentas o caídas en momentos importantes. Tampoco podemos asumir que sus cifras sean correctas, por eso la aplicación compara los números del texto con los datos calculados y advierte cuando no coinciden.

Lo que más nos dejó el laboratorio es que la IA acelera la escritura del código, pero la calidad depende de la especificación, de las pruebas y de la revisión humana.
