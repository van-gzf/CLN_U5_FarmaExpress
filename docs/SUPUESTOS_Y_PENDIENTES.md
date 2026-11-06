# Supuestos y pendientes (no se inventaron reglas)

Las pruebas solo verifican reglas aprobadas en la Unidad 3. Donde el reporte dejo una duda abierta,
se tomo una decision minima y se documenta aqui para validarla con el stakeholder.

| ID | Tema | Decision usada en el codigo | Fuente de la duda |
| --- | --- | --- | --- |
| S-01 | Dia exacto de caducidad | Caducado = fecha de caducidad **anterior** a hoy (T-02 de la matriz de trazabilidad). No hay prueba para "caduca hoy". | BRD 8: "fecha de vencimiento cumplida" es ambiguo |
| S-02 | FEFO y lotes caducados | FEFO elige el lote de caducidad mas proxima con existencia y **la venta se bloquea** si ese lote no es vendible (como el BPMN). No se omite el lote caducado. | Pregunta pendiente de la Etapa 5 |
| S-03 | Existencia minima | "Cae por debajo" = existencia **menor estricta** que la minima; igual al minimo no alerta. | RN-08 / US12 |
| S-04 | Datos de receta vacios | Un dato compuesto solo de espacios se considera vacio. | RN-06 |
| S-05 | Permiso para retirar lote | No se implementa; esta pendiente (H-01). | H-01 |
| S-06 | Cobro y ticket fiscal | No se modelan; por eso el servicio externo simulado es el despachador de eventos. | Pregunta pendiente Etapa 5 |

Nota de trazabilidad: los IDs RN-xx del Reporte U3 no coinciden con los del ADR (por ejemplo RN-03). Aqui se usan los del Reporte.
