"""Pruebas unitarias del dominio de FarmaExpress (sin base de datos, sin servicios externos).

Cada prueba cp_fxNN corresponde a una fila de docs/MATRIZ_CASOS_FARMAEXPRESS.csv.
Fecha fija HOY para que los resultados no varien con el reloj.
"""

from datetime import date

import pytest

from src.farmaexpress.domain import (
    AsignadorDeLotes,
    DatosDeReceta,
    DatosDeRecetaIncompletos,
    EvaluadorDeExistenciaMinima,
    LineaDeVenta,
    Lote,
    LoteRetirado,
    ProductoCaducado,
    SinExistencia,
    Venta,
    VentaYaCompletada,
)

HOY = date(2026, 11, 5)
SUC = "S1"


def lote(id_, caducidad, existencia=10, estado="VIGENTE", sucursal=SUC):
    return Lote(id_, "P1", caducidad, estado, {sucursal: existencia})


# ---------------- RN-02 / RN-03: no vender lotes caducados ni retirados
def test_cp_fx01_lote_vigente_descuenta_existencia():
    a = lote("A", date(2026, 11, 6))
    a.descontar(SUC, 2, HOY)
    assert a.existencia_en(SUC) == 8


def test_cp_fx02_lote_retirado_bloquea_venta_aunque_tenga_existencia():
    a = lote("A", date(2027, 1, 1), estado="RETIRADO")
    with pytest.raises(LoteRetirado):
        a.descontar(SUC, 1, HOY)
    assert a.existencia_en(SUC) == 10


def test_cp_fx03_lote_caducado_ayer_bloquea_venta():
    a = lote("A", date(2026, 11, 4))
    with pytest.raises(ProductoCaducado):
        a.descontar(SUC, 1, HOY)
    assert a.existencia_en(SUC) == 10


# ---------------- RN-05: asignacion FEFO
def test_cp_fx04_fefo_elige_el_lote_que_caduca_primero():
    a = lote("A", date(2027, 1, 10))
    b = lote("B", date(2027, 6, 10))
    assert AsignadorDeLotes().asignar([b, a], SUC, HOY).id == "A"


def test_cp_fx05_fefo_sin_lotes_con_existencia_rechaza():
    a = lote("A", date(2027, 1, 10), existencia=0)
    with pytest.raises(SinExistencia):
        AsignadorDeLotes().asignar([a], SUC, HOY)


def test_cp_fx06_fefo_omite_el_lote_proximo_si_no_tiene_existencia_en_la_sucursal():
    a = lote("A", date(2027, 1, 10), existencia=5, sucursal="S2")  # solo hay en otra sucursal
    b = lote("B", date(2027, 6, 10), existencia=3)
    assert AsignadorDeLotes().asignar([a, b], SUC, HOY).id == "B"


# ---------------- RN-06: datos de receta antes de completar la venta
def venta_con_receta():
    v = Venta("V1", SUC, "C1")
    v.agregar_linea(LineaDeVenta("P1", 1, "A", requiere_receta=True))
    return v


def test_cp_fx07_venta_con_receta_completa_se_completa():
    v = venta_con_receta()
    v.registrar_datos_de_receta(DatosDeReceta("1234567", "Dra. Perez", "F-001"))
    v.completar()
    assert v.estado == "COMPLETADA"


def test_cp_fx08_venta_con_receta_sin_folio_se_rechaza_y_sigue_abierta():
    v = venta_con_receta()
    v.registrar_datos_de_receta(DatosDeReceta("1234567", "Dra. Perez", ""))
    with pytest.raises(DatosDeRecetaIncompletos):
        v.completar()
    assert v.estado == "ABIERTA"


def test_cp_fx09_datos_de_receta_solo_espacios_se_consideran_vacios():
    v = venta_con_receta()
    v.registrar_datos_de_receta(DatosDeReceta("   ", "   ", "   "))
    with pytest.raises(DatosDeRecetaIncompletos):
        v.completar()


# ---------------- RN-08: alerta de resurtido
def test_cp_fx10_existencia_por_encima_del_minimo_no_genera_alerta():
    assert EvaluadorDeExistenciaMinima().evaluar("P1", SUC, 10, 5) is None


def test_cp_fx11_existencia_por_debajo_del_minimo_genera_alerta():
    alerta = EvaluadorDeExistenciaMinima().evaluar("P1", SUC, 2, 5)
    assert (alerta.producto_id, alerta.existencia, alerta.minima) == ("P1", 2, 5)


def test_cp_fx12_existencia_igual_al_minimo_no_genera_alerta():
    assert EvaluadorDeExistenciaMinima().evaluar("P1", SUC, 5, 5) is None


# ---------------- Invariantes adicionales del aggregate (no son parte de la matriz de 12)
def test_venta_completada_es_inmutable():
    v = Venta("V1", SUC, "C1")
    v.agregar_linea(LineaDeVenta("P1", 1, "A"))
    v.completar()
    with pytest.raises(VentaYaCompletada):
        v.agregar_linea(LineaDeVenta("P1", 1, "A"))


def test_venta_sin_lineas_no_se_completa():
    with pytest.raises(ValueError):
        Venta("V1", SUC, "C1").completar()


def test_cantidad_invalida_se_rechaza():
    a = lote("A", date(2027, 1, 1))
    with pytest.raises(ValueError):
        a.descontar(SUC, 0, HOY)
    with pytest.raises(ValueError):
        Venta("V1", SUC, "C1").agregar_linea(LineaDeVenta("P1", -1, "A"))


def test_descontar_mas_de_lo_disponible_rechaza():
    a = lote("A", date(2027, 1, 1), existencia=2)
    with pytest.raises(SinExistencia):
        a.descontar(SUC, 3, HOY)
    assert a.existencia_en(SUC) == 2


def test_venta_con_receta_sin_datos_registrados_se_rechaza():
    with pytest.raises(DatosDeRecetaIncompletos):
        venta_con_receta().completar()
