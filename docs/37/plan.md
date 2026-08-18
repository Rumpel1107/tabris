# Diseño — Tabris siempre encendido (ítem 37)

Fase 3 del método. Cada decisión se acordó en conversación antes de escribirse aquí.

## Enfoque

El despliegue es un directorio propio en `/opt/tabris`, dueño un usuario del sistema creado para eso. Dentro conviven tres cosas separadas: el **clon del código**, situado siempre en una etiqueta de versión; la **carpeta de datos**, fuera del alcance de git; y el **archivo de llaves**, que solo ese usuario puede leer.

El administrador de servicios del sistema mantiene el proceso vivo, lo levanta al arrancar el equipo y lo reintenta con espera creciente y acotada cuando falla. Tres temporizadores independientes ejecutan el respaldo diario, el purgado diario y la sonda de conexión.

Actualizar es ejecutar un guion versionado con una etiqueta: sitúa el código, actualiza dependencias, corre las pruebas dentro del propio despliegue y solo entonces reinicia. Volver atrás es el mismo guion con la etiqueta anterior.

## Cobertura

| AC | Dónde vive | Notas |
|---|---|---|
| AC1 — vuelve solo tras una falla | Definición del servicio: reinicio siempre | No solo ante error: también si termina limpiamente sin que nadie lo pidiera |
| AC2 — vuelve rápido tras interrupción larga | Definición del servicio: espera creciente con tope de 60 s y **sin límite de intentos** | El límite por defecto se rinde a los pocos reintentos; hay que desactivarlo explícitamente |
| AC3 — arranca con el equipo | Definición del servicio: habilitado al arranque, tras la red | Se verifica reiniciando de verdad, no leyendo que figura habilitado |
| AC4 — la copia de trabajo es irrelevante | Estructura de `/opt/tabris` | Producción no lee nada de la carpeta de desarrollo |
| AC5 — estado consultable | Administrador de servicios | Corriendo, desde cuándo y cuántos reinicios, sin código propio |
| AC6 — registros con fecha, sin contenido | Registro del sistema | Verificar en la fase 6 que ningún registro lleve texto de conversación |
| AC7 — copia íntegra diaria, 7 días | Guion de respaldo + su temporizador | Función de respaldo de la biblioteca estándar; nombre por fecha |
| AC8 — un respaldo fallido no interrumpe | Guion de respaldo | Registra y termina sin afectar al servicio |
| AC9 — purgado recuperable | Temporizador del purgado, con recuperación de ejecución pendiente | Ejecuta `purge-auto`, que ya existe del ítem 34c |
| AC10 — pruebas antes de entrar en servicio | Guion de despliegue, paso 3 | Si fallan, vuelve a la etiqueta anterior y no reinicia |
| AC11 — versión identificable y reversible | Clon situado en etiqueta | Volver atrás = mismo guion, etiqueta anterior |
| AC12 — desplegar y volver atrás sin internet | Clon de producción | Volver atrás nunca necesita red; traer una versión nueva sí |
| AC13 — flujo de ramas y etiquetas | Convención de trabajo, no código | `main` → fusión a rama de producción → etiqueta |
| AC14 — usuario propio | Creación del usuario en el despliegue | Sin sesión interactiva ni permisos administrativos |
| AC15 — llaves no expuestas | Archivo de variables leído por el administrador de servicios | Nunca en la definición del servicio ni en la lista de procesos |
| AC16 — base copiada íntegra al arrancar | Primer paso del despliegue, con el guion de respaldo | La copia inicial usa el mismo mecanismo que el respaldo diario |
| AC17 — el servicio ejecuta solo Discord | Definición del servicio | El chat por línea de comandos queda en desarrollo |
| AC18 — sonda de conexión | Guion de la sonda + su temporizador, cada 5 min | Escribe al registro del sistema, no a un formato propio |
| AC19 — herramientas de operador como el usuario del servicio | Convención de uso | Son la única vía manual que escribe en la base de producción |

## Decisiones

| # | Elegido | Descartado | Por qué |
|---|---|---|---|
| D1 | Servicio nativo del sistema | Contenedor | Un contenedor depende de que su motor arranque, y una capa más entre el fallo y la causa. El servicio nativo vuelve al arrancar el equipo sin depender de nada más |
| D2 | Un directorio de despliegue con el clon dentro y los datos al lado | Todo dentro del clon | El comando que limpia archivos no versionados borraría la base, y se teclea justo cuando algo va raro en el repositorio |
| D3 | `/opt/tabris` | Carpeta personal de un usuario del sistema; repartir en tres rutas del sistema | Los directorios personales son para personas y las herramientas los tratan distinto; repartir dispersa lo que tiene que viajar junto |
| D4 | Usuario del sistema propio, sin acceso a nada ajeno | Grupo compartido con el usuario personal | El chat necesita las llaves; si el usuario personal puede lanzarlo, cualquier extensión o agente que corra como él puede leerlas |
| D5 | Temporizadores del sistema | `cron` | Solo los temporizadores recuperan de forma nativa la ejecución que no corrió con el equipo apagado (AC9); su salida cae en el mismo registro y su estado es consultable |
| D6 | Un temporizador por tarea | Uno que las ejecute todas | Un fallo del respaldo no debe arrastrar al purgado, y la sonda tiene otro ritmo |
| D7 | Respaldo con la función de la biblioteca estándar de Python | Comando de línea de SQLite; copia compactada | El comando exige instalar una herramienta del sistema en cada máquina nueva; compactar reescribe el archivo entero para ganar kilobytes irrelevantes |
| D8 | El despliegue verifica que existan las variables que `.env.example` declara | Confiar en que se recuerde añadirlas | Un proveedor nuevo desplegado sin su variable arranca roto: las pruebas usan simulaciones y no lo detectan |
| D9 | Solo la carpeta de datos se hace configurable por entorno | Hacer configurable también la ruta del archivo de llaves | El administrador de servicios ya entrega las variables al proceso; sería código nuevo para lograr lo que el sistema hace gratis |
| D10 | Si las pruebas fallan, el guion devuelve el clon a la etiqueta en servicio | Dejarlo en la etiqueta nueva | Si no, el despliegue miente sobre qué versión corre, y el primer reinicio arranca la versión rota sin que nadie lo decida |
| D11 | El guion nunca toca datos ni llaves | Que el despliegue sincronice todo el directorio | Actualizar debe ser seguro por construcción, no por cuidado al teclear |
| D12 | El respaldo abre la copia y verifica que sea legible | Dar por buena la copia escrita | Una copia corrupta ocupa el lugar de la buena en la rotación |

## Conceptos nuevos

Todos explicados durante la fase 2 y la fase 3, antes de decidir sobre ellos.

- **Etiqueta de versión frente a rama** — una rama es un puntero que se mueve; una etiqueta marca un punto fijo. Es lo que permite responder "qué versión corre" y volver atrás con una sola acción.
- **Usuario del sistema y permisos de archivo** — un usuario sin sesión interactiva, dueño del despliegue. Los permisos no protegen de quien ya es administrador: compartimentan, para que un problema de un lado no alcance el otro.
- **Espera creciente con tope** — reintentar cada vez más espaciado, pero sin pasar de un máximo, para que una interrupción larga no deje el servicio dormido después de que todo volvió.
- **Recuperación de ejecución pendiente** — un temporizador que, al arrancar, nota que su ejecución no ocurrió y la lanza, en vez de saltarla hasta el día siguiente.

## Qué deja desactualizado

- **`README.md`** — hoy solo explica cómo arrancar Tabris a mano. Debe documentar que existe un despliegue permanente y cómo se actualiza.
- **`CONTRIBUTING.md`** — añadir que las rutas de datos salen de la configuración y son ajustables por entorno, para que no vuelvan a escribirse fijas.
- **`.env.example`** — pasa de ser documentación a ser la fuente que el despliegue verifica (D8); mantenerlo al día deja de ser cortesía.

## Riesgos

- **El servicio arranca pero no funciona.** Las pruebas pasan y el proceso vive, pero el bot no conecta —por ejemplo, un token vencido—. El estado del servicio diría "corriendo". Lo revelaría escribirle desde Discord, que es lo que exige la fase 6.
- **Los registros podrían llevar contenido de conversaciones.** Hoy no deberían, pero pasan a guardarse en disco durante días. Se verifica leyendo los registros reales tras una conversación, no revisando el código.
- **La copia inicial de la base se hace una sola vez.** Si se hace mal, se arrastra. Se verifica comparando cuentas, hechos y mensajes entre origen y copia antes de dar por buena la puesta en marcha.
- **El equipo podría no levantar todo al arrancar.** Un servicio puede figurar como habilitado y aun así no iniciarse hasta que algo se lo pida. Solo un reinicio real lo demuestra.

---

**Compuerta de salida**

- [x] Cada criterio de aceptación tiene dónde vivir
- [x] Las decisiones registran la alternativa descartada
- [x] Los conceptos nuevos se explicaron y se entendieron
- [x] Lo que queda desactualizado está listado
- [x] Cada afirmación se confirmó en conversación antes de escribirse
