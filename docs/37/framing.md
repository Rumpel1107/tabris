# Encuadre — Tabris siempre encendido (ítem 37)

Fase 1 del método. Registro de decisiones, alcance y limitantes. El razonamiento y la
evidencia que llevaron a cada punto se discutieron en su momento y no se reproducen aquí.

## Investigación

- Tabris exige Python 3.13 o superior. `tools/setup.sh` construye el entorno completo desde cero, así que un despliegue no necesita pasos previos propios.
- La base de datos usa WAL desde el ítem 34: los cambios recientes viven en un archivo lateral hasta consolidarse. Una copia a nivel de archivo puede quedar incompleta o inconsistente sin que se note — parece válida y falla al restaurar. Solo el comando de respaldo propio de SQLite garantiza una copia íntegra.
- El proyecto no tiene hoy unidad de servicio, tarea programada ni guion de despliegue. Se ejecuta a mano y termina con la sesión que lo lanzó.
- El código de desarrollo y lo que se ejecuta son hoy el mismo directorio, de modo que un cambio a medio escribir queda a un reinicio de distancia de ejecutarse, y las pruebas comparten los datos del uso real.

## Problema

Tabris solo funciona mientras alguien lo lanza a mano y esa sesión sigue abierta. Al cerrarla o al reiniciar, el proceso desaparece sin aviso y la ausencia se descubre al escribirle y no obtener respuesta. Además incumple una promesa ya construida: el borrado a los 14 días del ítem 34c depende de una tarea diaria desatendida que hoy no tiene dónde ejecutarse, así que una cuenta dada de baja esperaría indefinidamente.

## Para quién es

Cualquier instancia en uso diario, con una o más cuentas activas.

No cubre despliegues que ofrezcan un compromiso de disponibilidad hacia terceros: eso exige redundancia que este ítem no aborda.

## Evidencia de que importa

- El AC5 del ítem 34c exige una tarea diaria desatendida y el proyecto no tiene ninguna.
- Nada respalda la base con el comando propio de SQLite, único método íntegro con WAL activo.
- Un proceso lanzado a mano no sobrevive a un reinicio ni al cierre de la sesión, y no deja rastro de que se detuvo.

## Restricciones que el diseño debe respetar

- **Si un respaldo no se puede completar, queda registrado y el servicio sigue funcionando.**
- **El despliegue vive separado del código de desarrollo y es autocontenido:** actualizar o borrar la copia de trabajo no altera lo que está corriendo.
- **El proceso corre con su propio usuario del sistema, sin permisos sobre nada ajeno al despliegue.** Limita lo que un fallo o un abuso de Tabris puede alcanzar.
- **El despliegue se ejecuta paso a paso y comentado, y cada paso confirmado queda escrito en un guion versionado**, de modo que repetirlo en otra máquina no dependa de la memoria de nadie.
- **La forma se elige pensando en que otros proyectos la reutilicen**, sin construir todavía nada genérico: eso espera al segundo caso real (§9 del PLAN).
- **La documentación del proyecto describe el mecanismo, nunca el entorno donde corre** (`AGENTS.md`).

## Fuera de alcance

- **Elección de proveedor de hospedaje (ítem 36).** Se retoma cuando exista un compromiso de disponibilidad hacia terceros o algo público que servir de forma continua.
- **Publicar aplicaciones web** con dominio y certificado.
- **Tareas de administración ejecutadas por Tabris (ítem 38a).** Este ítem deja el camino posible; construirlo es otro ítem, con su propia lista cerrada de comandos permitidos.
- **Avisos al operador (ítem 38).** Sin ellos una falla se descubre mirando. Se acepta a sabiendas.
- **Retención automática de mensajes viejos** (ítem 34c parte 3).
- **Audio, visión y Telegram** (ítems 34a, 34b, 34d).
- **Mantenimiento del sistema anfitrión** que no sea de Tabris.

## Decisión

**Construir ahora**, sobre la infraestructura ya disponible y sin costo adicional. Todo lo que se produzca —unidad de servicio, permisos, respaldo, tarea diaria y guion de despliegue— es válido sin cambios en cualquier otro anfitrión.

Revisar la decisión cuando ocurra cualquiera de estas dos: que existan usuarios cuya operación dependa del servicio, o que haya algo público que servir de forma continua.

---

**Compuerta de salida**

- [x] Investigación hecha y con fuentes
- [x] El problema cabe en un párrafo que un extraño entiende
- [x] El anti-alcance está nombrado
- [x] Hay evidencia más allá de la intuición del dueño
- [x] Cada afirmación del documento se confirmó en conversación antes de escribirse
