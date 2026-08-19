# Tareas — Tabris siempre encendido (ítem 37)

Fase 4 del método. Orden de ejecución, no de tema: el número es el orden en que se hace.

## Rebanadas

| # | Rebanada | Cubre | Cómo se verifica | Hecho |
|---|---|---|---|---|
| 1 | **Rutas de datos configurables por entorno** — la carpeta de datos sale de una variable, con el valor actual como predeterminado; base, identidad y exports derivan de ella. Incluye la línea en `CONTRIBUTING.md` | D9 | Correr la aplicación de desarrollo apuntada a otra carpeta y ver que la usa; suite verde sin cambios en desarrollo | ✅ |
| 2 | **Guion de respaldo** — copia con la función de la biblioteca estándar, nombre por fecha, rotación de 7 días, verificación de que la copia se abre, y registro sin interrumpir si falla | AC7, AC8, D7, D12 | Correrlo contra la base de desarrollo, abrir la copia y comparar su contenido con el origen | ✅ |
| 3 | **El despliegue** — usuario del sistema, `/opt/tabris`, rama de producción con su primera etiqueta, clon, ambiente propio, archivo de llaves y copia inicial de la base con el guion de la rebanada 2 | AC4, AC13, AC14, AC15, AC16, D2, D3, D4 | La suite completa corre verde dentro del despliegue, como ese usuario; cuentas, hechos y mensajes coinciden entre la base original y la copia | ⬜ |
| 4 | **El servicio** — definición, reinicio siempre con espera creciente acotada y sin límite de intentos, arranque junto con el equipo, ejecutando solo el canal de Discord | AC1, AC2, AC3, AC5, AC6, AC17, D1 | Tabris responde en Discord desde el despliegue; matar el proceso y verlo volver; **reiniciar el equipo de verdad** y comprobar que vuelve solo; leer los registros y confirmar que no llevan texto de conversaciones | ⬜ |
| 5 | **Temporizadores diarios** — respaldo y purgado, separados, con recuperación de la ejecución pendiente | AC9, D5, D6 | Dispararlos a mano y comprobar la copia y la rotación; comprobar que una ejecución no realizada se recupera al arrancar | ⬜ |
| 6 | **Sonda de conexión** — comprobación periódica que registra si el exterior era alcanzable | AC18 | Correrla y leer lo que dejó en el registro; provocar un fallo y ver que queda anotado | ⬜ |
| 7 | **Guion de despliegue** — etiqueta, código, dependencias, pruebas, reinicio; vuelta atrás; verificación de las variables que declara `.env.example`. Incluye el `README.md` | AC10, AC11, AC12, D8, D10, D11 | Liberar una versión nueva de verdad con el guion, y volver a la anterior con el mismo guion | ⬜ |

## Notas

- **Las rebanadas 1 y 2 son código puro** y se hacen con la disciplina de siempre —prueba en rojo primero— sin tocar el sistema. Todo lo demás se apoya en ellas.
- **La 7 va al final a propósito.** El guion de despliegue se escribe a partir de lo que se ejecutó a mano en las rebanadas 3 y 4. No se puede escribir bien un procedimiento que no se ha ejecutado nunca; el guion es el residuo de haberlo hecho, no su plan previo.
- **El nombre del respaldo sale del reloj del equipo.** Si ese reloj no está en hora local, la copia de la tarde queda con la fecha del día siguiente. Se decide en la rebanada 4, al ver los registros del servicio con hora.
- **La rebanada 4 es el hito.** A partir de ahí Tabris deja de depender de que alguien mantenga una terminal abierta.
- **Cada rebanada se ejecuta paso a paso y comentada**, y cada paso confirmado queda escrito, según lo acordado en la fase 1.
- **El aviso a los usuarios tras una caída no está aquí.** Es el ítem 37a, que se construye justo después de cerrar este.

---

**Compuerta de salida**

- [x] Rebanadas en orden de ejecución
- [x] Cada rebanada dice cómo se verifica
- [x] Ninguna rebanada deja código que nadie llama
- [x] Cada afirmación se confirmó en conversación antes de escribirse
