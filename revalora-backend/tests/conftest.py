"""Fixtures compartidas.

Las pruebas usan SQLite en memoria (no necesitan PostgreSQL) y un cliente de IA
falso, así que no dependen del servicio revalora-ia-service.
"""

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models import ActividadEconomica, Base, CategoriaMaterial, Rol
from app.schemas.ia_schema import (
    RespuestaOportunidadesIA,
    RespuestaRecomendacionIA,
    RespuestaReconocimientoIA,
)
from app.services.ia.ia_service_client import obtener_ia_client
from app.utils.constantes import ACTIVIDADES_BASE, CATEGORIAS_BASE, ROLES_BASE

# PNG válido de 1x1 píxel.
PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d4944415478da63f8cfc0f01f0005000201a2f1d5e5"
    "0000000049454e44ae426082"
)


class IaFalsa:
    """Sustituye a IaServiceClient. Cada prueba fija las respuestas que necesita."""

    def __init__(self) -> None:
        self.reconocimiento = RespuestaReconocimientoIA(
            material="madera",
            confianza=0.93,
            predicciones=[
                {"material": "madera", "confianza": 0.93},
                {"material": "carton", "confianza": 0.05},
            ],
        )
        self.recomendacion = RespuestaRecomendacionIA(
            producto="marco para cuadros",
            materiales=[
                {"material": "madera", "funcion": "estructura"},
                {"material": "vidrio", "funcion": "protección"},
                {"material": "carton", "funcion": "respaldo"},
            ],
        )
        self.oportunidades = RespuestaOportunidadesIA(productos=[])
        self.error: Exception | None = None
        self.llamadas: list[tuple[str, object]] = []

    def _responder(self, nombre: str, argumento: object, respuesta):
        self.llamadas.append((nombre, argumento))
        if self.error is not None:
            raise self.error
        return respuesta

    def reconocer_material(self, contenido: bytes, nombre_archivo: str, tipo_mime: str):
        return self._responder("reconocimiento", tipo_mime, self.reconocimiento)

    def recomendar_materiales(self, descripcion: str):
        return self._responder("recomendacion", descripcion, self.recomendacion)

    def sugerir_oportunidades(self, materiales: list[str], max_productos: int):
        return self._responder("oportunidades", materiales, self.oportunidades)


def _sembrar(db: Session) -> None:
    db.add_all(Rol(nombre=n, descripcion=d) for n, d in ROLES_BASE)
    db.add_all(CategoriaMaterial(codigo=c, nombre=n, descripcion=d) for c, n, d in CATEGORIAS_BASE)
    db.add_all(ActividadEconomica(codigo=c, nombre=n) for c, n in ACTIVIDADES_BASE)
    db.commit()


@pytest.fixture
def engine() -> Iterator[Engine]:
    motor = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(motor)
    yield motor
    motor.dispose()


@pytest.fixture
def sesiones(engine: Engine) -> sessionmaker[Session]:
    fabrica = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with fabrica() as db:
        _sembrar(db)
    return fabrica


@pytest.fixture
def db(sesiones: sessionmaker[Session]) -> Iterator[Session]:
    with sesiones() as sesion:
        yield sesion


@pytest.fixture
def ia() -> IaFalsa:
    return IaFalsa()


@pytest.fixture(autouse=True)
def uploads_temporales(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Las fotos subidas en las pruebas se guardan en una carpeta temporal."""
    monkeypatch.setitem(settings.__dict__, "ruta_uploads", tmp_path)
    return tmp_path


@pytest.fixture
def client(sesiones: sessionmaker[Session], ia: IaFalsa) -> Iterator[TestClient]:
    def _db() -> Iterator[Session]:
        with sesiones() as sesion:
            yield sesion

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[obtener_ia_client] = lambda: ia
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- ayudantes


@pytest.fixture
def registrar(client: TestClient) -> Callable[..., dict[str, str]]:
    """Crea una cuenta y devuelve las cabeceras de autenticación."""

    def _registrar(email: str = "ana@taller.co", nombre: str = "Ana") -> dict[str, str]:
        respuesta = client.post(
            "/api/v1/auth/registro",
            json={"nombre": nombre, "email": email, "password": "clave-segura-1"},
        )
        assert respuesta.status_code == 201, respuesta.text
        client.cookies.clear()
        return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}

    return _registrar


@pytest.fixture
def crear_empresa(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> Callable[..., dict[str, str]]:
    """Crea una cuenta con empresa y devuelve sus cabeceras de autenticación."""

    def _crear(
        email: str,
        nombre: str = "Empresa",
        latitud: float | None = 4.65,
        longitud: float | None = -74.05,
        ciudad: str = "Bogotá",
    ) -> dict[str, str]:
        cabeceras = registrar(email=email, nombre=nombre)
        respuesta = client.post(
            "/api/v1/empresas",
            headers=cabeceras,
            json={
                "nombre": nombre,
                "tipo": "MICROEMPRESA",
                "ubicacion": {"ciudad": ciudad, "latitud": latitud, "longitud": longitud},
            },
        )
        assert respuesta.status_code == 201, respuesta.text
        return cabeceras

    return _crear


@pytest.fixture
def categoria_id(client: TestClient) -> Callable[[str], int]:
    categorias = {c["codigo"]: c["id"] for c in client.get("/api/v1/categorias").json()}
    return lambda codigo: categorias[codigo]


@pytest.fixture
def publicar_material(
    client: TestClient, categoria_id: Callable[[str], int]
) -> Callable[..., dict]:
    def _publicar(cabeceras: dict[str, str], **datos) -> dict:
        cuerpo = {
            "categoria_id": categoria_id(datos.pop("categoria", "madera")),
            "titulo": "Retazos de madera de pino",
            "cantidad": "20",
            "unidad_medida": "UNIDAD",
            "estado": "BUENO",
            "tipo_oferta": "VENTA",
            "precio": "1500",
        }
        cuerpo.update(datos)
        respuesta = client.post("/api/v1/materiales", headers=cabeceras, json=cuerpo)
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _publicar


@pytest.fixture
def publicar_necesidad(
    client: TestClient, categoria_id: Callable[[str], int]
) -> Callable[..., dict]:
    def _publicar(cabeceras: dict[str, str], **datos) -> dict:
        cuerpo = {
            "categoria_id": categoria_id(datos.pop("categoria", "madera")),
            "titulo": "Necesito madera para marcos",
            "cantidad": "10",
            "unidad_medida": "UNIDAD",
            "estado_minimo": "REGULAR",
            "presupuesto_maximo": "50000",
        }
        cuerpo.update(datos)
        respuesta = client.post("/api/v1/necesidades", headers=cabeceras, json=cuerpo)
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _publicar
