# Spec — Baja de cuenta y borrado de datos (ítem 34c, parte 2)

Fase 2 del método. Vista desde afuera únicamente. Archivo de trabajo, no commitear.

## Propósito y alcance

Una persona puede pedir que se la elimine de Tabris. Su cuenta se desactiva apenas el operador procesa el pedido, deja de conversar, y recibe una copia de todos sus datos. Pasados 14 días, una tarea programada borra su información de forma permanente e irreversible, junto con esa copia. Dentro de esos 14 días la baja se puede deshacer.

**Dónde decide un humano:** en la desactivación, y solo ahí. El borrado posterior es la consecuencia automática de esa decisión, no una decisión nueva.

**Deliberadamente fuera de alcance:**

- **No se dispara desde el chat.** Ni la desactivación, ni la restauración, ni el borrado. La conversación solo lee el estado de la cuenta, nunca lo modifica.
- **No incluye la entrega del archivo** al usuario (correo, link o adjunto). Se genera el archivo; hacérselo llegar depende del despliegue y se especifica cuando exista.
- **No incluye enganchar la tarea al programador del servidor.** El borrado se construye para correr sin intervención, pero atarlo a un horario necesita un host siempre encendido (ítems 36-38). Hasta entonces el operador lo dispara a mano, con el mismo comportamiento.
- **No incluye la retención automática** de mensajes viejos — es la parte 3 del ítem 34c, trabajo aparte.
- **No incluye "ver mis datos" a pedido** — descartado con razón escrita: el perfil y los hechos ya viajan frescos en cada turno.

## Flujo (camino feliz)

Participan dos actores: **la persona** que pide la baja y **el operador** que la ejecuta.

1. La persona solicita formalmente la baja. El pedido llega **por fuera de Tabris** (correo o mensaje directo al operador).
2. El operador desactiva la cuenta. Ve un resumen de a quién está dando de baja y lo confirma explícitamente. Queda registrada la fecha del pedido, que es la que fija el vencimiento.
3. En el mismo acto se genera el archivo con todos los datos de esa persona y se le hace llegar. Tenerlo desde el primer día le deja la ventana completa para guardarlo.
4. Desde ese instante la cuenta deja de conversar. Si la persona escribe por cualquier canal, Tabris le responde que su cuenta está pendiente de eliminación, le da la fecha límite y le explica que si se arrepintió debe contactar al operador.
5. Si la persona se arrepiente antes del vencimiento, el operador reactiva la cuenta y todo vuelve exactamente como estaba: perfil, hechos e historial intactos. El archivo de export se destruye, porque el motivo para conservarlo desapareció.
6. Pasado el vencimiento, una tarea programada ejecuta el borrado sin intervención humana. Desaparecen los datos de la persona y su archivo de export.

## Estados de falla

| Estado | Qué detecta el sistema | Qué ve el usuario | Qué puede hacer |
|---|---|---|---|
| Persona desactivada escribe durante la ventana | La cuenta está desactivada | Aviso de baja pendiente con la fecha límite y la indicación de contactar al operador | Contactar al operador para restaurar; esperar al vencimiento |
| Persona desactivada escribe desde otro canal vinculado | Misma cuenta, mismo estado | El mismo aviso, idéntico en todos los canales | Igual que arriba |
| Se desactiva una cuenta ya desactivada | El estado ya estaba puesto | *(operador)* Aviso de que ya estaba desactivada, con su fecha original | Nada. **El plazo no se reinicia**: vale la primera fecha |
| Se intenta borrar a mano una cuenta que nunca se desactivó | Falta el estado | *(operador)* La operación se rechaza sin tocar nada | Desactivarla primero y esperar el plazo |
| Se intenta borrar a mano antes del vencimiento | La fecha límite es futura | *(operador)* Rechazo, mostrando cuánto falta | Esperar, o indicar explícitamente que quiere saltarse el plazo |
| Se intenta operar sobre alguien que no existe | Sin coincidencia | *(operador)* Rechazo | Verificar a quién le está apuntando |
| La confirmación escrita no coincide | El texto tecleado no es el esperado | *(operador)* Se aborta sin desactivar nada | Reintentar |
| No se pudo generar el archivo de datos | El export falló | *(operador)* Rechazo; **la cuenta queda activa** | Reintentar. Nadie se da de baja sin llevarse su copia |
| El borrado se interrumpe a mitad | La operación no llegó al final | *(operador)* Error en el registro | **Queda todo o no queda nada**, nunca a medias. Reintentar |
| La tarea programada corre y no hay ninguna cuenta vencida | Ninguna coincidencia | Nada | Nada. Es el caso normal la mayoría de los días |
| La tarea programada no corrió (host caído, servicio detenido) | **Nada lo detecta solo** | Nada | **Riesgo real:** los datos se retienen más allá de lo prometido y nadie se entera. Necesita visibilidad del lado del operador (ítem 38, alertas) |
| Persona reactivada vuelve a escribir | La cuenta está activa | Conversación normal, con su memoria intacta | Nada |

## Criterios de aceptación

- **AC1** — Dado que una cuenta está activa, cuando el operador la desactiva, entonces primero ve un resumen de a quién está dando de baja y debe confirmarlo explícitamente; recién entonces queda registrada la fecha del pedido y la cuenta deja de conversar.
- **AC2** — Dado que una cuenta está desactivada, cuando la persona escribe por cualquier canal, entonces recibe el aviso de baja pendiente con su fecha límite, **y ese intercambio no se guarda** (una cuenta desactivada no genera datos nuevos).
- **AC3** — Dado que una cuenta está desactivada y el plazo no venció, cuando el operador la reactiva, entonces vuelve a conversar normalmente conservando perfil, hechos e historial, y su archivo de export se destruye.
- **AC4** — Dado que se está desactivando una cuenta, cuando la baja se completa, entonces existe un archivo con perfil, canales vinculados, hechos y todos los mensajes de esa persona; si el archivo no se pudo generar, la cuenta no se desactiva.
- **AC5** — Dado que hay cuentas desactivadas cuyo plazo venció, cuando corre la tarea de borrado, entonces las borra sin intervención humana.
- **AC6** — Dado que hay cuentas desactivadas cuyo plazo **no** venció, cuando corre la tarea de borrado, entonces no las toca.
- **AC7** — Dado que se borra una cuenta, cuando la operación termina, entonces no queda ningún rastro de esa persona en ninguna parte del sistema —incluido su archivo de export— y la operación es todo-o-nada.
- **AC8** — Dado que una cuenta no está desactivada, cuando se intenta borrarla, entonces la operación se rechaza.
- **AC8b** — Dado que una cuenta está desactivada pero su plazo no venció, cuando el operador intenta borrarla a mano, entonces se rechaza, salvo que indique explícitamente que quiere saltarse el plazo.
- **AC9** — Dado cualquier momento y cualquier canal, cuando alguien pide por chat que se borre o desactive una cuenta, entonces no existe ningún camino que lo ejecute.

## Preguntas abiertas

| # | Pregunta | Estado | Resolución / por qué se difiere |
|---|---|---|---|
| 1 | ¿Cuánto dura la ventana de gracia? | resuelta | **14 días.** Alineado con Discord, que es donde están los testers. Cabe holgado en los 15 días hábiles de la Ley 1581 |
| 2 | ¿Qué ve un usuario desactivado que escribe? | resuelta | Aviso con fecha límite; la restauración se pide al operador. El chat solo lee el estado |
| 3 | ¿Qué lleva el archivo de datos? | resuelta | Todo: perfil, canales, hechos y mensajes completos. Es lo que honestamente significa "tus datos" |
| 4 | ¿Cómo se le hace llegar el archivo? | **diferida** | Depende del despliegue (ítems 36-38). Las opciones evaluadas —link en el VPS con URL no adivinable, o adjunto por Discord— quedan escritas en `temp.md` |
| 4b | ¿Quién ejecuta el borrado al vencer el plazo? | resuelta | **Una tarea programada, sin intervención.** Evita que un olvido del operador retenga datos más allá de lo prometido. La compuerta humana se mueve a la desactivación, que es donde realmente se decide |
| 4c | ¿A qué hora exacta vence el plazo? | resuelta | **Al final del día** (23:59 UTC) del último día, no a la hora en que se pidió la baja. La política se enuncia en días: mostrar una fecha y borrar a media mañana promete un día que la persona no tiene. Además el purgado corre una vez al día, así que una hora exacta es una precisión que el programador no puede honrar. Salvedad: se usa UTC, que para husos muy al este podría mostrar el día siguiente — no aplica a los usuarios actuales |
| 5 | ¿Se guardan los mensajes de alguien desactivado? | resuelta *(propuesta)* | **No.** Una cuenta dada de baja no debería generar datos nuevos que después haya que borrar |
| 6 | ¿Re-desactivar reinicia el plazo? | resuelta *(propuesta)* | **No.** Vale la fecha del primer pedido; si no, un pedido repetido posterga el borrado sin querer |
| 7 | ¿Se puede borrar antes de que venza el plazo? | resuelta *(propuesta)* | **Sí, con indicación explícita.** La ventana es una cortesía hacia la persona; si pide que sea inmediato, esperar 14 días no la protege de nada |
| 8 | ¿Retención automática de mensajes viejos? | **diferida** | Es la parte 3 del ítem 34c, con su propio ciclo |
| 9 | ¿Qué pasa con el archivo de export una vez entregado? | resuelta | **Vive exactamente lo mismo que la ventana:** nace al desactivar y se destruye al borrar, o antes si la cuenta se reactiva. Por seguridad de la persona y para no conservar información de terceros más de lo necesario |
| 10 | ¿Cómo se entera el operador si la tarea programada dejó de correr? | **diferida** | Sin visibilidad, los datos se retienen de más y nadie lo nota. Va con las alertas al operador ya previstas en el ítem 38 |

---

**Compuerta de salida**

- [x] Criterios de aceptación en forma Dado/Cuando/Entonces
- [x] Estados de falla enumerados, no implícitos
- [x] Toda pregunta abierta resuelta o diferida con razón
- [x] Sin decisiones técnicas filtradas en este documento
