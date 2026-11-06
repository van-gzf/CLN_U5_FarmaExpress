import pytest

from src import repository
from src.farmaexpress import infrastructure


@pytest.fixture(autouse=True)
def cerrar_motores_de_prueba(monkeypatch):
    motores = []
    for modulo in (repository, infrastructure):
        original = modulo.create_engine

        def con_registro(*args, _original=original, **kwargs):
            motor = _original(*args, **kwargs)
            motores.append(motor)
            return motor

        monkeypatch.setattr(modulo, "create_engine", con_registro)
    yield
    for motor in motores:
        motor.dispose()