"""Integracion: SQLAlchemy (SQLite en memoria), Unit of Work y mock del despachador de eventos.

FarmaExpress no tiene pasarela de pago modelada (cobro y ticket fiscal quedaron como
pregunta pendiente en la Unidad 3), asi que el servicio externo simulado es el
DespachadorDeEventos, que si forma parte del diseno (ADR-002).
"""

from datetime import date
from unittest.mock import Mock

import pytest

from src.farmaexpress.application import LoteNoEncontrado, RetirarLoteHandler
from src.farmaexpress.domain import EventoLoteRetirado, Lote
from src.farmaexpress.infrastructure import SqlUnitOfWork, make_engine


def lote_en_dos_sucursales():
    return Lote("L1", "P1", date(2027, 3, 1), existencias={"S1": 10, "S2": 4})


def sembrar(engine, lote):
    with SqlUnitOfWork(engine) as uow:
        uow.lotes.guardar(lote)
        uow.confirmar()


def leer(engine, lote_id):
    with SqlUnitOfWork(engine) as uow:
        return uow.lotes.obtener_por_id(lote_id)


def test_cp_fx13_commit_persiste_el_lote_con_sus_existencias():
    engine = make_engine()
    sembrar(engine, lote_en_dos_sucursales())
    guardado = leer(engine, "L1")
    assert guardado.existencias == {"S1": 10, "S2": 4}
    assert guardado.estado == "VIGENTE"


def test_cp_fx14_rollback_descarta_el_cambio():
    engine = make_engine()
    with SqlUnitOfWork(engine) as uow:
        uow.lotes.guardar(lote_en_dos_sucursales())
        uow.revertir()
    assert leer(engine, "L1") is None


def test_retirar_lote_aplica_a_todas_las_sucursales_y_publica_evento():
    engine = make_engine()
    sembrar(engine, lote_en_dos_sucursales())
    despachador = Mock()
    handler = RetirarLoteHandler(lambda: SqlUnitOfWork(engine), despachador)
    handler.ejecutar("L1", "alerta sanitaria")
    assert leer(engine, "L1").estado == "RETIRADO"
    assert leer(engine, "L1").existencias == {"S1": 10, "S2": 4}
    despachador.publicar.assert_called_once_with(EventoLoteRetirado("L1", "alerta sanitaria"))


class UowQueFallaAlConfirmar(SqlUnitOfWork):
    def confirmar(self):
        raise RuntimeError("fallo de base de datos")


def test_cp_fx15_evento_no_se_publica_si_el_commit_falla_y_el_lote_no_cambia():
    engine = make_engine()
    sembrar(engine, lote_en_dos_sucursales())
    despachador = Mock()
    handler = RetirarLoteHandler(lambda: UowQueFallaAlConfirmar(engine), despachador)
    with pytest.raises(RuntimeError):
        handler.ejecutar("L1", "alerta sanitaria")
    despachador.publicar.assert_not_called()
    assert leer(engine, "L1").estado == "VIGENTE"


def test_cp_fx16_retirar_lote_inexistente_falla_sin_publicar_evento():
    engine = make_engine()
    despachador = Mock()
    with pytest.raises(LoteNoEncontrado):
        RetirarLoteHandler(lambda: SqlUnitOfWork(engine), despachador).ejecutar("X", "motivo")
    despachador.publicar.assert_not_called()


def test_guardar_actualiza_existencias_de_un_lote_ya_guardado():
    engine = make_engine()
    sembrar(engine, lote_en_dos_sucursales())
    with SqlUnitOfWork(engine) as uow:
        lote = uow.lotes.obtener_por_id("L1")
        lote.existencias["S1"] = 7
        lote.existencias["S3"] = 1
        uow.lotes.guardar(lote)
        uow.confirmar()
    assert leer(engine, "L1").existencias == {"S1": 7, "S2": 4, "S3": 1}
