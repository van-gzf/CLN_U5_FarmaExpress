"""Capa de aplicacion: un Handler por caso de uso (Etapas 4 y 6 de la Unidad 3)."""

from .domain import EventoLoteRetirado


class LoteNoEncontrado(Exception):
    pass


class RetirarLoteHandler:
    """CU-04: retirar un lote en todas las sucursales.

    El evento se publica solo DESPUES de confirmar la transaccion (ADR-002).
    El permiso de quien retira esta pendiente de validar (H-01), no se implementa.
    """

    def __init__(self, uow_factory, despachador):
        self.uow_factory = uow_factory
        self.despachador = despachador

    def ejecutar(self, lote_id: str, motivo: str) -> None:
        with self.uow_factory() as uow:
            lote = uow.lotes.obtener_por_id(lote_id)
            if lote is None:
                raise LoteNoEncontrado(lote_id)
            lote.retirar()
            uow.lotes.guardar(lote)
            uow.confirmar()
        self.despachador.publicar(EventoLoteRetirado(lote_id, motivo))
