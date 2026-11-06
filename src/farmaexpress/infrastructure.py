"""Infraestructura: repositorio SQLAlchemy y Unit of Work (ADR-02)."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from sqlalchemy.pool import StaticPool

from .domain import Lote


class Base(DeclarativeBase):
    pass


class LoteRow(Base):
    __tablename__ = "lotes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    producto_id: Mapped[str] = mapped_column(String, nullable=False)
    caducidad: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False)
    existencias: Mapped[list["ExistenciaRow"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class ExistenciaRow(Base):
    __tablename__ = "existencias"
    lote_id: Mapped[str] = mapped_column(ForeignKey("lotes.id"), primary_key=True)
    sucursal_id: Mapped[str] = mapped_column(String, primary_key=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)


def make_engine(url="sqlite+pysqlite:///:memory:"):
    engine = create_engine(url, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return engine


class SqlLoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def obtener_por_id(self, lote_id: str):
        row = self.session.get(LoteRow, lote_id)
        if row is None:
            return None
        return Lote(
            id=row.id,
            producto_id=row.producto_id,
            caducidad=row.caducidad,
            estado=row.estado,
            existencias={e.sucursal_id: e.cantidad for e in row.existencias},
        )

    def guardar(self, lote: Lote) -> None:
        row = self.session.get(LoteRow, lote.id)
        if row is None:
            row = LoteRow(id=lote.id, existencias=[])
            self.session.add(row)
        row.producto_id = lote.producto_id
        row.caducidad = lote.caducidad
        row.estado = lote.estado
        actuales = {e.sucursal_id: e for e in row.existencias}
        for sucursal_id, cantidad in lote.existencias.items():
            if sucursal_id in actuales:
                actuales[sucursal_id].cantidad = cantidad
            else:
                row.existencias.append(ExistenciaRow(sucursal_id=sucursal_id, cantidad=cantidad))


class SqlUnitOfWork:
    """Una transaccion por caso de uso: confirmar() hace commit, revertir() rollback."""

    def __init__(self, engine):
        self.engine = engine

    def __enter__(self):
        self.session = Session(self.engine)
        self.lotes = SqlLoteRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.session.rollback()
        self.session.close()
        return False

    def confirmar(self) -> None:
        self.session.commit()

    def revertir(self) -> None:
        self.session.rollback()
