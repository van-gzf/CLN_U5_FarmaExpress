# CLN · Unidad 5 · Integración, Pruebas y Calidad — FarmaExpress (Equipo 10)

Proyecto Python con pruebas automatizadas (pytest), cobertura (pytest-cov), lint (Ruff) y CI (GitHub Actions).
Contiene dos partes:

1. **Proyecto base del laboratorio** (`src/domain.py`, `application.py`, `repository.py`, `security.py`): pedidos, cobro con mock,
   persistencia y autorizacion. Pasos 1 a 8 del laboratorio.
2. **Adaptacion al PIA** (`src/farmaexpress/`): reglas de FarmaExpress de la Unidad 3. Paso 9.

## Instalacion y comandos

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -v
python -m ruff check src tests
python -m pytest -v --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=80
```
En macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`. El reporte HTML queda en `htmlcov/index.html`.

## Arquitectura (FarmaExpress)

- `domain.py`: Domain Model (ADR-01). Aggregates `Lote` y `Venta`; Value Object `DatosDeReceta`; servicios de dominio
  `AsignadorDeLotes` (FEFO) y `EvaluadorDeExistenciaMinima`; evento `EventoLoteRetirado`. No importa SQLAlchemy.
- `application.py`: Handler por caso de uso (`RetirarLoteHandler`, CU-04). Publica el evento **despues** del commit (ADR-02).
- `infrastructure.py`: `SqlLoteRepository` y `SqlUnitOfWork` sobre SQLAlchemy con SQLite en memoria.

## Reglas probadas y trazabilidad

| Regla (Reporte U3) | Pruebas | Archivo |
| --- | --- | --- |
| RN-02 / RN-03 no vender caducados ni retirados | CP-FX01 a 03 | tests/test_farma_dominio.py |
| RN-05 FEFO | CP-FX04 a 06 | tests/test_farma_dominio.py |
| RN-06 datos de receta | CP-FX07 a 09 | tests/test_farma_dominio.py |
| RN-08 existencia minima | CP-FX10 a 12 | tests/test_farma_dominio.py |
| Persistencia, rollback y mock de eventos | CP-FX13 a 16 | tests/test_farma_integracion.py |

Matriz completa: `docs/MATRIZ_CASOS_FARMAEXPRESS.csv`. Supuestos y pendientes: `docs/SUPUESTOS_Y_PENDIENTES.md`.
Evidencias E1 a E9: `docs/EVIDENCIAS.md`. Uso de IA: `docs/BITACORA_IA.md`.

## Limitaciones
No hay API, interfaz ni pruebas E2E reales. SQLite en memoria no sustituye pruebas contra el motor productivo.
