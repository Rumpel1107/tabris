# Diseño — Baja de cuenta y borrado de datos (ítem 34c, parte 2)

Fase 3 del método. Cómo se construye y qué se rechazó. Archivo de trabajo, no commitear.

## Enfoque

Tres piezas, siguiendo la separación que ya tiene el proyecto:

- **`core/db.py`** gana las operaciones crudas: una columna nueva en `users` que marca la baja, y un borrado total que corre en una sola transacción.
- **`core/account.py`** (módulo nuevo) tiene la lógica del ciclo de vida: dar de baja, restaurar, exportar, y purgar las cuentas vencidas. No imprime ni pregunta nada.
- **`tools/admin.py`** es un adaptador delgado, igual que los canales: interpreta los argumentos, muestra el resumen, pide la confirmación e imprime resultados. Es el único que habla con una persona.

La conversación solo gana un guardia de lectura en `safe_handle_turn`, junto al tope de longitud y el límite de ráfaga que ya viven ahí.

## Cobertura

| AC | Dónde vive | Notas |
|---|---|---|
| AC1 — desactivar con confirmación | `admin.py` (resumen + confirmación) → `core/account.deactivate_account` → columna nueva en `users` | La confirmación es escribir el nombre de la persona, no un "sí" |
| AC2 — desactivado escribe, nada se guarda | Guardia en `safe_handle_turn` + clave nueva en `core/strings.py` | Devuelve antes de `handle_turn`, así que no toca modelo ni base. Aplica a la persona en su canal de siempre; quien llegue esquivando el bloqueo no recibe nada |
| AC3 — restaurar conserva todo | `core/account.reactivate_account` + `admin.py` | Limpia la marca y borra el archivo de export |
| AC4 — el export existe o no hay baja | `core/account.export_user` orquestado dentro de `deactivate_account` | El archivo se escribe primero; si falla, la marca no se pone |
| AC5 — la tarea borra lo vencido sin intervención | `core/account.purge_due_accounts` + subcomando de `admin.py` | Sin `input()` en este camino |
| AC6 — no toca lo que no venció | La consulta de selección dentro de `purge_due_accounts` | Es la línea que más merece una prueba por mutación |
| AC7 — sin rastro, todo o nada | `core/db.delete_user_completely` (una transacción) + borrado del archivo | Orden obligado por las llaves foráneas |
| AC8 — cuenta activa no se borra | `core/account` | Rechazo antes de tocar nada |
| AC8b — antes del plazo solo con indicación explícita | Bandera en `admin.py` → `core/account` | El camino automático nunca la usa |
| AC9 — ningún camino desde el chat | Ausencia de tool, fijada por una prueba sobre la lista de tools | Un criterio negativo necesita una prueba que lo sostenga, o se rompe sin que nadie lo note |

## Decisiones

| # | Elegido | Rechazado | Por qué |
|---|---|---|---|
| D1 | **Una sola columna `deactivated_at` en `users`** (nula = activa) | Una columna `status` aparte, o `status` + fecha | Los únicos dos estados son activa y pendiente de baja, y la fecha hace falta igual para calcular el vencimiento. Una fecha nula dice "activa" sin ambigüedad. Si algún día aparece un tercer estado, se agrega ahí |
| D2 | **El guardia va en `safe_handle_turn`** | Ponerlo en cada adaptador | Es el punto de entrada agnóstico al canal, y ya es donde viven el tope de longitud y el límite de ráfaga. Un canal nuevo hereda el guardia sin escribir nada |
| D3 | **El guardia lee la fila del usuario por su cuenta** | Leerla una vez y pasarla hacia adentro para ahorrar una consulta | Ahorra una lectura local de SQLite a cambio de cambiar la firma de `handle_turn` y tocar sus pruebas. No vale el canje |
| D4 | **`tools/admin.py`, con subcomandos, y `setup.sh` se muda ahí también** | Dejarlo en la raíz; o cuatro scripts sueltos | `setup.sh` ya era una herramienta de operador viviendo en la raíz, así que la carpeta nace con dos archivos y no repite la objeción que descartó a `docs/` en su momento. Cuatro scripts multiplican la raíz que se acaba de ordenar |
| D4b | **`setup.sh` sube un nivel al mudarse** (`cd "$(dirname "$0")/.."`) | Moverlo tal cual | Hoy hace `cd` a su propia carpeta y todo lo demás es relativo a la raíz: `requirements.txt`, `.env`, `data/`, pytest. Movido sin tocar esa línea, rompe el arranque de quien clona el repo, en silencio |
| D5 | **Borrado duro de verdad** | Marcar inactivo, como se hace con hechos y mensajes | Un borrado de privacidad en blando deja los datos ahí. Es una excepción consciente a la regla de `CONTRIBUTING.md`, y hay que escribirla ahí |
| D6 | **Sin respaldo especial antes de purgar** | Copiar la base antes de cada borrado y guardarla N días | Un respaldo de lo que acabamos de prometer borrar contradice la promesa. El respaldo periódico del ítem 38 ya cubre el caso de un error, y lo honesto es declarar en los términos que las copias pueden retener datos un tiempo corto — es exactamente lo que declara Discord |
| D7 | **El archivo de export se llama por el id de la persona** | Un nombre aleatorio | Restaurar y purgar tienen que encontrarlo sin buscar. Cuando exista la entrega por link, el nombre no adivinable será cosa de esa capa, no de esta |
| D8 | **Al desactivar se vencen los códigos de vinculación activos** | Dejarlos vivos | Cierra el hueco en el origen: sin código válido, y sin poder pedir uno nuevo porque la cuenta no conversa, no queda camino para vincular un canal. Usa el mismo `UPDATE` que ya corre al crear un código |
| D8b | **`redeem_link_code` además rechaza una cuenta dada de baja** | Confiar solo en D8 | Segunda capa, por si un canje llega en el mismo instante en que se procesa la baja. Misma lógica de capas del cercado de memoria: cerrar en el origen y dejar una red |

## Conceptos nuevos

- **Subcomandos en la línea de comandos.** Hasta ahora todo se arranca sin argumentos (`python -m channels.cli`). `admin.py` necesita saber qué hacer y sobre quién: `admin.py deactivate 3`, `admin.py purge`. Python trae una herramienta estándar para esto que valida los argumentos y genera la ayuda sola; no hay que interpretar texto a mano.
- **Un criterio negativo necesita prueba propia.** AC9 dice que algo *no* debe existir. Nada falla solo si mañana alguien agrega esa tool; hace falta una prueba que afirme qué tools hay, y que se ponga roja cuando aparezca una que borre cuentas.
- **La tensión de los respaldos.** Cualquier copia de seguridad conserva lo que se borró, hasta que la copia rota. No es un error del diseño, es inherente: se resuelve declarándolo, no evitándolo.

## Qué queda desactualizado

Se corrige en el mismo cambio, no después:

- **`CONTRIBUTING.md`** — la regla de que nunca se borra en duro necesita su excepción escrita.
- **`README.md`** — aparece un punto de entrada nuevo y cambia el comando de arranque (`./setup.sh` → `./tools/setup.sh`); la regla de `AGENTS.md` pide actualizarlo en el mismo cambio.
- **`AGENTS.md`** — su sección de arranque nombra `./setup.sh` en la raíz.
- **`.gitignore`** — la carpeta de exports guarda datos personales en texto plano y hoy nada la excluye. Los patrones actuales (`*.db*`, `*_client_id`) no la cubren.
- **`PLAN.md`** — el ítem 34c y su fecha.
- **`config.py`** — la constante de la ventana de gracia.

## Riesgos

- **Un error en la consulta de selección borra a quien no debía, sin nadie mirando.** Es el riesgo central de automatizar. Se ataja con prueba por mutación sobre esa consulta: se rompe a propósito y se confirma que una prueba lo caza.
- **El guardia agrega una lectura por turno.** Local y barata, pero es real; si alguna vez pesa, D3 dice por dónde se optimiza.
- **La tarea programada deja de correr y nadie se entera** (ya está en la spec como pregunta diferida al ítem 38).
- **Alguien desactivado abre una cuenta nueva desde otro canal.** No lo impide nada y no debería: es una persona distinta a los ojos del sistema. Distinto de D8, que es reconectar la cuenta vieja.

---

**Compuerta de salida**

- [x] Cada criterio de aceptación tiene un hogar
- [x] Las decisiones registran la alternativa rechazada
- [ ] Conceptos nuevos explicados y entendidos
- [x] Artefactos desactualizados listados
