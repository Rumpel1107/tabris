# Spec — Tabris siempre encendido (ítem 37)

Fase 2 del método. Vista desde afuera únicamente. Cada punto se acordó en conversación
antes de escribirse aquí.

## Propósito y alcance

Tabris pasa de ser un programa que alguien lanza a mano a un servicio administrado: arranca solo, vuelve solo tras una falla, respalda su base y ejecuta el purgado diario que el ítem 34c dejó pendiente. El despliegue vive separado del código de desarrollo y se actualiza con un procedimiento escrito y repetible.

**Deliberadamente fuera de alcance:** elegir proveedor de hospedaje (ítem 36); publicar aplicaciones web con dominio y certificado; que Tabris ejecute tareas de administración (ítem 38a); avisos automáticos al operador (ítem 38); el aviso a los usuarios tras una caída (ítem 37a); retención de mensajes viejos (ítem 34c parte 3); audio, visión y Telegram.

## Flujo (camino feliz)

1. El operador ejecuta el procedimiento de despliegue paso a paso. Cada paso se comenta antes de correrlo y queda escrito en un guion versionado.
2. El despliegue queda situado en una versión etiquetada, con su propio ambiente, su propia base —copiada íntegramente de la existente— y su propio archivo de llaves.
3. La suite de pruebas corre dentro del despliegue. Solo si pasa, el servicio entra en operación.
4. El servicio queda encendido y responde en el canal de Discord. Sobrevive al cierre de la sesión del operador y al reinicio del equipo.
5. Una vez al día se produce una copia íntegra de la base y se descarta la más antigua de la rotación.
6. Una vez al día se ejecuta el purgado de cuentas vencidas.
7. Para liberar una versión nueva: se fusiona lo probado, se etiqueta, y el despliegue se sitúa en la etiqueta nueva. El servicio se interrumpe el tiempo que tarda en reiniciar.

## Estados de falla

| Estado | Qué detecta el sistema | Qué ve el usuario | Qué puede hacer |
|---|---|---|---|
| El proceso muere por un fallo | La salida del proceso, y cuántas veces ha ocurrido | Nada, salvo que escriba en esa ventana | Nada: el servicio vuelve por sí solo |
| Sin conexión, de minutos a horas | Nada nuestro está corriendo o está aislado | Escribe y nunca recibe respuesta | Reenviar cuando vuelva. El aviso de recuperación es el ítem 37a |
| Reinicio del equipo | El servicio arranca sin intervención | Posible silencio durante el arranque | Reenviar si no obtuvo respuesta |
| El respaldo no se puede completar | El fallo queda registrado | Nada | Nada: el servicio sigue funcionando |
| El purgado no corre a su hora | Al arrancar, que la ejecución quedó pendiente | Nada | Nada: se recupera automáticamente |
| Pruebas rojas al desplegar | La suite falla antes de poner la versión en servicio | Nada: sigue la versión anterior | Corregir y volver a desplegar |
| La versión nueva falla ya en servicio | Nada avisa por su cuenta | Fallos o silencio | El operador vuelve a la etiqueta anterior |
| Cuenta desactivada escribe | La cuenta está desactivada (ítem 34c) | Aviso de baja pendiente con su fecha límite | Contactar al operador o esperar el vencimiento |

## Criterios de aceptación

- **AC1** — Dado que el servicio está en operación, cuando el proceso termina por una falla, entonces vuelve a estar operativo sin intervención humana.
- **AC2** — Dado que una interrupción externa impide operar, cuando las condiciones se restablecen, entonces el servicio queda funcionando en menos de un minuto, sin importar si la interrupción duró minutos u horas, y ninguna interrupción puede dejarlo detenido de forma permanente.
- **AC3** — Dado que el equipo se reinicia, cuando termina de arrancar, entonces el servicio queda operativo sin que nadie inicie sesión.
- **AC4** — Dado que existe una copia de trabajo del código, cuando se modifica o se borra, entonces lo que está en servicio no se altera.
- **AC5** — Dado que el servicio está en operación, cuando se consulta al sistema, entonces se puede saber si está corriendo, desde cuándo y cuántas veces se ha reiniciado, sin leer código ni registros.
- **AC6** — Dado cualquier momento posterior, cuando se revisan los registros del servicio, entonces contienen lo que el servicio escribió, con fecha, sobreviviendo a reinicios del proceso y del equipo, y **nunca el texto de las conversaciones**: solo metadatos y errores.
- **AC7** — Dado que la base está en uso, cuando corre el respaldo diario, entonces produce una copia íntegra por un mecanismo que no consiste en copiar el archivo, la deja fuera del directorio de despliegue, y conserva las de los últimos 7 días rotando.
- **AC8** — Dado que un respaldo no se puede completar, cuando falla, entonces queda registrado y el servicio sigue funcionando.
- **AC9** — Dado que el purgado diario no pudo ejecutarse a su hora porque el equipo estaba apagado, cuando el equipo arranca, entonces la ejecución pendiente se recupera, de modo que una cuenta vencida nunca espera más que la duración del apagón.
- **AC10** — Dado un despliegue nuevo, cuando se pone una versión en servicio, entonces la suite de pruebas pasó antes dentro del propio despliegue; si falla, la versión anterior sigue en servicio.
- **AC11** — Dado un despliegue en operación, cuando se pregunta qué versión corre, entonces la respuesta es una etiqueta concreta; y cuando esa versión resulta defectuosa, volver a la anterior es una sola acción documentada.
- **AC12** — Dado que no hay conexión a internet, cuando se despliega o se vuelve atrás, entonces ambas operaciones funcionan igual.
- **AC13** — Dado el flujo de versiones, cuando se libera, entonces el cambio llegó a la rama de producción por fusión desde la rama de desarrollo y quedó etiquetado; la rama de producción nunca recibe cambios directos.
- **AC14** — Dado el servicio en operación, cuando se inspecciona con qué permisos corre, entonces usa un usuario propio del sistema sin acceso a nada ajeno al despliegue.
- **AC15** — Dadas las llaves de producción, cuando se busca su contenido en la definición del servicio, en la lista de procesos o en la salida de cualquier guion del despliegue, entonces no aparece; viven en un archivo propio legible solo por el usuario del servicio.
- **AC16** — Dado el arranque del despliegue, cuando se compara su base con la existente, entonces contiene una copia íntegra de esta; desde ese momento los datos de desarrollo y de producción son independientes.
- **AC17** — Dado el servicio administrado, cuando se revisa qué ejecuta, entonces ejecuta el canal de Discord y nada más. Las personas llegan a su perfil de producción únicamente por ese canal; la interfaz de chat por línea de comandos no se usa contra producción y sigue siendo herramienta de desarrollo, sobre datos de desarrollo.
- **AC19** — Dadas las herramientas de operador, cuando actúan sobre los datos de producción, entonces se ejecutan como el usuario del servicio; ninguna otra vía manual escribe en esa base, y hacerlo mientras el servicio corre no la corrompe.
- **AC18** — Dado que la disponibilidad de la conexión no está medida, cuando pasa un periodo de operación normal, entonces existe un registro periódico de si el exterior era alcanzable, revisable después y sobreviviendo a reinicios, suficiente para estimar cuánto tiempo estuvo incomunicado el servicio.

## Preguntas abiertas

| # | Pregunta | Estado | Resolución / por qué se difiere |
|---|---|---|---|
| 1 | ¿A qué hora corre el purgado diario? | resuelta | Una vez al día; la hora concreta es un parámetro y se fija en el diseño |
| 2 | ¿Cuánto debe durar una caída para justificar avisar a los usuarios? | **diferida** | Pertenece al ítem 37a, que se construye justo después |
| 3 | ¿Cómo se entera el operador de que algo falló? | **diferida** | Ítem 38. Hasta entonces, descubrir una falla exige mirar, y se acepta a sabiendas |
| 4 | ¿Cuánto se cae realmente la conexión? | resuelta | **Se mide.** Hoy solo hay estimaciones, y de ese dato depende decidir algún día si conviene otro anfitrión. Una comprobación periódica lo registra; su resultado no condiciona ningún otro criterio |
| 5 | ¿Se cifra el almacenamiento? | **descartada** | Solo protege ante sustracción física del equipo, escenario posible pero muy poco probable aquí. No aporta valor hoy y se elimina como variable |
| 6 | ¿Qué pasa con la copia de trabajo cuando el proyecto se congela? | resuelta | Es indiferente: el despliegue no depende de ella. Borrarla o conservarla no cambia el servicio |
| 7 | ¿Se generaliza el procedimiento para otros proyectos? | resuelta | No todavía. La forma se elige pensando en que se reutilice, pero no se construye nada genérico antes del segundo caso real (§9 del PLAN) |

---

**Compuerta de salida**

- [x] Criterios de aceptación en forma Dado / Cuando / Entonces
- [x] Estados de falla enumerados, no implícitos
- [x] Cada pregunta abierta resuelta o diferida con razón
- [x] Ninguna decisión técnica se filtró a este documento
- [x] Cada afirmación se confirmó en conversación antes de escribirse
