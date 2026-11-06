"""Dominio de FarmaExpress (Domain Model, ADR-01 / Unidad 3).

Reglas de la Unidad 3 que se implementan aqui:
RN-02 / RN-03  no vender lotes caducados ni retirados
RN-05          asignacion de lote con FEFO
RN-06          datos de receta (cedula, medico, folio) antes de completar la venta
RN-08          alerta de resurtido bajo la existencia minima
Los supuestos de diseno estan en docs/SUPUESTOS_Y_PENDIENTES.md
"""

from dataclasses import dataclass, field
from datetime import date


class ProductoCaducado(Exception):
    pass


class LoteRetirado(Exception):
    pass


class SinExistencia(Exception):
    pass


class DatosDeRecetaIncompletos(Exception):
    pass


class VentaYaCompletada(Exception):
    pass


# ---------------------------------------------------------------- Lote
@dataclass
class Lote:
    id: str
    producto_id: str
    caducidad: date
    estado: str = "VIGENTE"  # VIGENTE | RETIRADO
    existencias: dict = field(default_factory=dict)  # sucursal_id -> cantidad

    def esta_caducado(self, hoy: date) -> bool:
        # Caducado se deduce de la fecha (Etapa 3): caducidad anterior a hoy.
        return self.caducidad < hoy

    def existencia_en(self, sucursal_id: str) -> int:
        return self.existencias.get(sucursal_id, 0)

    def verificar_vendible(self, hoy: date) -> None:
        if self.estado == "RETIRADO":
            raise LoteRetirado(f"el lote {self.id} esta retirado")
        if self.esta_caducado(hoy):
            raise ProductoCaducado(f"el lote {self.id} esta caducado")

    def descontar(self, sucursal_id: str, cantidad: int, hoy: date) -> None:
        if cantidad <= 0:
            raise ValueError("la cantidad debe ser mayor que cero")
        self.verificar_vendible(hoy)
        disponible = self.existencia_en(sucursal_id)
        if disponible < cantidad:
            raise SinExistencia(f"lote {self.id}: hay {disponible}, se pidieron {cantidad}")
        self.existencias[sucursal_id] = disponible - cantidad

    def retirar(self) -> None:
        # El retiro aplica al lote completo, en todas las sucursales (RN-03).
        self.estado = "RETIRADO"


# ------------------------------------------------------ Asignador FEFO
class EstrategiaFEFO:
    """First Expired, First Out: primero el lote con caducidad mas proxima."""

    def elegir(self, lotes, sucursal_id: str) -> Lote:
        candidatos = [lote for lote in lotes if lote.existencia_en(sucursal_id) > 0]
        if not candidatos:
            raise SinExistencia("no hay lotes con existencia en la sucursal")
        return min(candidatos, key=lambda lote: lote.caducidad)


class AsignadorDeLotes:
    def __init__(self, estrategia=None):
        self.estrategia = estrategia or EstrategiaFEFO()

    def asignar(self, lotes, sucursal_id: str, hoy: date) -> Lote:
        lote = self.estrategia.elegir(lotes, sucursal_id)
        lote.verificar_vendible(hoy)  # la venta se bloquea si el lote no es vendible
        return lote


# --------------------------------------------------------------- Venta
@dataclass(frozen=True)
class DatosDeReceta:
    cedula: str = ""
    medico: str = ""
    folio: str = ""

    def esta_completo(self) -> bool:
        return all(valor and valor.strip() for valor in (self.cedula, self.medico, self.folio))


@dataclass
class LineaDeVenta:
    producto_id: str
    cantidad: int
    lote_id: str
    requiere_receta: bool = False


@dataclass
class Venta:
    id: str
    sucursal_id: str
    cajero_id: str
    lineas: list = field(default_factory=list)
    receta: DatosDeReceta | None = None
    estado: str = "ABIERTA"  # ABIERTA | COMPLETADA (ticket inmutable, RN-07)

    def _exigir_abierta(self) -> None:
        if self.estado != "ABIERTA":
            raise VentaYaCompletada("una venta completada no puede modificarse")

    def agregar_linea(self, linea: LineaDeVenta) -> None:
        self._exigir_abierta()
        if linea.cantidad <= 0:
            raise ValueError("la cantidad debe ser mayor que cero")
        self.lineas.append(linea)

    def registrar_datos_de_receta(self, datos: DatosDeReceta) -> None:
        self._exigir_abierta()
        self.receta = datos

    def completar(self) -> None:
        self._exigir_abierta()
        if not self.lineas:
            raise ValueError("la venta necesita al menos una linea")
        necesita_receta = any(linea.requiere_receta for linea in self.lineas)
        if necesita_receta and not (self.receta and self.receta.esta_completo()):
            raise DatosDeRecetaIncompletos("faltan cedula, medico o folio de la receta")
        self.estado = "COMPLETADA"


# ------------------------------------------- Existencia minima (RN-08)
@dataclass(frozen=True)
class AlertaDeResurtido:
    producto_id: str
    sucursal_id: str
    existencia: int
    minima: int


class EvaluadorDeExistenciaMinima:
    def evaluar(self, producto_id, sucursal_id, existencia, minima):
        # "cae por debajo" se interpreta de forma estricta: existencia < minima.
        if existencia < minima:
            return AlertaDeResurtido(producto_id, sucursal_id, existencia, minima)
        return None


# ------------------------------------------------------ Eventos de dominio
@dataclass(frozen=True)
class EventoLoteRetirado:
    lote_id: str
    motivo: str
