# Tareas — Baja de cuenta y borrado de datos (ítem 34c, parte 2)

Fase 4 del método. Orden de ejecución, no de tema: el número es el orden en que se hace.

## Rebanadas

| # | Rebanada | Cubre | Cómo se verifica | Hecho |
|---|---|---|---|---|
| 1 | **Mudar `setup.sh` a `tools/`** — crea la carpeta, sube un nivel el `cd`, y actualiza `README.md` y `AGENTS.md` | D4, D4b | Correr `./tools/setup.sh` de punta a punta: arma el entorno, aplica permisos y deja la suite verde. Leer el README y confirmar que el comando que promete es el que existe | ✅ |
| 2 | **Exportar los datos de una persona** — `core/account.export_user` + subcomando `export` + regla en `.gitignore` | AC4 (parcial) | Exportar el usuario real contra la base de verdad y abrir el archivo: perfil, canales, hechos y mensajes completos. Confirmar que `git status` no ofrece el archivo | ✅ |
| 3 | **El sistema respeta la baja** — columna `deactivated_at` con migración, constante de la ventana, guardia en `safe_handle_turn`, texto es/en, y la prueba que fija AC9 | AC2, AC9 | Marcar la columna a mano en una base de prueba y escribirle a Tabris desde el CLI: llega el aviso con la fecha límite y la conversación no queda guardada. La prueba de AC9 se pone roja si se agrega una tool que borre cuentas | ✅ |
| 4 | **Dar de baja desde la herramienta** — `core/account.deactivate_account` (vence códigos, exige export previo, marca la fecha) + subcomando `deactivate` con resumen y confirmación + rechazo del canje (D8b) | AC1, AC4, D8, D8b | Dar de baja una cuenta de prueba: pide confirmación escrita, crea el archivo, marca la fecha y deja sin efecto el código de vinculación que estuviera activo. Intentar canjear ese código y ver que falla | ✅ |
| 5 | **Restaurar** — `core/account.reactivate_account` + subcomando `reactivate`, que además borra el archivo de export | AC3 | Restaurar la cuenta dada de baja en la rebanada 4 y volver a conversar desde el CLI: responde normal y conserva perfil, hechos e historial. El archivo ya no está | ⬜ |
| 6 | **Borrar de verdad** — `core/db.delete_user_completely` en una transacción, `core/account.purge_due_accounts`, subcomando `purge` con la bandera para saltarse el plazo, y la excepción escrita en `CONTRIBUTING.md` | AC5, AC6, AC7, AC8, AC8b, D5 | Sobre una base de prueba con varias cuentas: purgar y confirmar que la vencida no deja rastro en ninguna tabla y que la no vencida queda intacta. Prueba por mutación sobre la consulta de selección | ⬜ |

## Notas

- **La rebanada 3 va antes que la 4 a propósito.** Primero el sistema aprende a respetar la marca, después aparece la herramienta que la pone. Al revés existiría una ventana donde se puede dar de baja a alguien y el chat le sigue contestando como si nada.
- **La rebanada 2 va antes que la 4** porque dar de baja exige que el export ya exista y funcione (AC4): si el archivo no se puede generar, la baja no se completa.
- **La rebanada 1 no aporta funcionalidad**, pero crea la carpeta que usan la 2, 4, 5 y 6, y arrastra consigo los cambios de documentación. Hacerla después obligaría a mover un archivo recién escrito.
- **Nada de esto engancha la tarea a un horario.** La rebanada 6 deja el borrado listo para correr sin intervención; atarlo al programador del servidor depende del despliegue (ítems 36-38).
- **AC8b (saltarse el plazo) no tiene camino automático.** Solo existe como bandera explícita en la herramienta; el `purge` programado nunca la usa.

---

**Compuerta de salida**

- [x] Rebanadas en orden de ejecución
- [x] Cada rebanada dice cómo se verifica
- [x] Ninguna rebanada deja código que nadie llama
