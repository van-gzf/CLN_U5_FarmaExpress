# Evidencias E1–E9 (Laboratorio guiado, Unidad 5)

> Las capturas las tomas tu en tu computadora; aqui van los textos y tablas ya preparados. Revisalos y ajusta con tus palabras.

## E1 · Entorno y primera ejecucion
**Captura:** terminal con `python -m pytest -v` y el resumen `44 passed`.
**Explicacion (3 lineas):** pytest descubre las funciones `test_*`, las ejecuta y reporta cuales pasan o fallan. El entorno virtual (venv)
aisla las bibliotecas del curso para que el proyecto sea reproducible en cualquier equipo.

## E2 · Pruebas unitarias nuevas
Pruebas: `test_vip_discount_200`, `test_regular_200_no_discount` (tests/test_order.py). **Captura:** `python -m pytest tests/test_order.py -v` en PASSED.

| Entrada | Regla | Esperado | Real |
| --- | --- | --- | --- |
| total 200, VIP | VIP 15% | cobro 170, descuento 30 | 170 / 30 (PASSED) |
| total 200, regular | sin descuento | cobro 200 | 200 (PASSED) |

## E3 · TDD (RED, GREEN, REFACTOR)
La prueba `test_cannot_confirm_twice` ya esta en el repo. **Para obtener la captura RED real:**
1. En `src/domain.py`, dentro de `confirm()`, comenta la primera linea: `# self._reject_if_already_confirmed()`.
2. Ejecuta `python -m pytest -v`. Debe fallar **solo** `test_cannot_confirm_twice` (DID NOT RAISE ValueError). **Captura RED.**
3. Descomenta la linea y ejecuta de nuevo: todo en PASSED. **Captura GREEN.**
4. El REFACTOR ya esta hecho: la validacion vive en dos metodos privados (`_reject_if_already_confirmed`, `_validate_total_and_debt`) sin cambiar el comportamiento.

**Fragmento:** `if self.status == "CONFIRMED": raise ValueError("already confirmed")`.
**Por que TDD no es ejecutar pruebas despues:** la prueba escrita primero define el comportamiento esperado y se ve fallar antes de programar;
asi se comprueba que la prueba realmente detecta el defecto y el codigo se limita a lo necesario.

## E4 · Base de datos: commit y rollback
Prueba: `test_repository_commit_order_250` (id=2, total 250, estado NEW). **Captura:** PASSED.
**Commit vs rollback:** `commit` vuelve persistente el cambio dentro de la transaccion; `rollback` lo descarta y deja la base como estaba
(`test_repository_rollback` consulta y obtiene `None`). Solo se uso SQLite en memoria, nunca datos reales.

## E5 · Mock de la pasarela de pago
Rutas: aprobada (`test_gateway_approved`) y rechazada VIP de 200 (`test_gateway_rejected_vip_200`: `charge` se llama con 170 y se lanza RuntimeError).
El mock no transmite dinero; solo simula la respuesta del servicio externo.
**Riesgo anotado:** `checkout()` confirma el pedido antes de saber si el pago fue aceptado, asi que un pago rechazado deja el pedido en CONFIRMED.
**Propuesta:** calcular el importe sin cambiar el estado, cobrar, y confirmar solo si el cobro fue exitoso (o revertir el estado con una compensacion si el cobro falla).

## E6 · Autorizacion (`can_cancel`)
| Rol | Propietario | Estado | Antiguedad | Resultado |
| --- | --- | --- | --- | --- |
| Admin | No | SHIPPED | cualquiera | Denegado (enviado nunca se cancela) |
| Admin | No | NEW | 48 h | Permitido |
| Dueno | Si | NEW | 1 h | Permitido |
| Dueno | Si | NEW | 23 h 59 min | Permitido |
| Dueno | Si | NEW | exactamente 24 h | Denegado |
| Dueno | Si | NEW | 25 h | Denegado |
| Tercero | No | NEW | reciente | Denegado |

## E7 · Cobertura y calidad
**Capturas:** `python -m ruff check src tests` (All checks passed) y `pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=80` (100 %), mas `htmlcov/index.html`.
**Rama aun no probada (explicacion honesta):** la cobertura es de lineas, no de comportamiento; 100 % no significa 0 defectos. Quedan sin probar:
la venta concurrente del mismo lote (el reporte propone control optimista de concurrencia, no implementado), el permiso para retirar lotes (H-01) y el estado de cuarentena.

## E8 · GitHub Actions
Sube el proyecto y captura: ejecucion **verde**, luego cambia una asercion a falsa (por ejemplo `assert o.confirm() == 86` en `test_vip_discount`), push y captura **roja**,
revierte, push y captura **verde**. Pega aqui la URL del repositorio: ______.
**Que detecto el pipeline:** al romper la aserción, el paso `pytest` fallo y marco la ejecucion en rojo impidiendo dar por buena la version; al revertirla volvio a verde.
Aclaracion: bloquear el merge requiere configurar branch protection en GitHub; el YAML por si solo no lo activa.

## E9 · Adaptacion al PIA (FarmaExpress)
Matriz: `docs/MATRIZ_CASOS_FARMAEXPRESS.csv` (16 casos: 12 de reglas + 4 de integracion). Pruebas: `tests/test_farma_dominio.py` y `tests/test_farma_integracion.py`.
Cobertura del codigo pertinente (`src/farmaexpress/`): 100 %.
**Decisiones de diseno:** el dominio no importa SQLAlchemy (Domain Model, ADR-01); el Unit of Work define el limite transaccional y el evento se publica solo tras el commit (ADR-02);
FarmaExpress no tiene servicio de cobro modelado, por eso el mock se aplica al despachador de eventos; las dudas abiertas se documentaron como supuestos en `SUPUESTOS_Y_PENDIENTES.md` en lugar de inventar reglas.

## Reflexion final (150–200 palabras; ajustala con tu voz)
El defecto mas costoso en FarmaExpress seria dispensar un medicamento caducado o de un lote retirado, o vender un medicamento controlado sin los datos de la receta.
Un lote caducado puede danar la salud de un paciente y generar sanciones sanitarias, y el BRD establece cero ventas de este tipo como criterio de exito. Un error asi podria pasar
inadvertido porque el sistema "funciona": abre, cobra y emite el ticket, pero incumple la regla. Las pruebas CP-FX02 y CP-FX03 lo evitan: verifican que un lote retirado o
caducado se rechaza con un error de negocio y que la existencia no cambia. De igual forma, CP-FX08 y CP-FX09 comprueban que no se completa una venta con receta incompleta. Tambien aprendi
que la cobertura del 100 % no demuestra correccion funcional: lo importante es que cada regla aprobada tenga pruebas de exito, error y limite, y que el pipeline las ejecute en cada cambio.
Ademas, documentar los supuestos evita inventar reglas que el cliente no ha aprobado.
