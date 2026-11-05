"""Pruebas del repositorio de materiales sobrantes."""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import (
    CategoriaMaterial,
    DisponibilidadMaterial,
    Empresa,
    EstadoMaterial,
    MaterialSobrante,
    Rol,
    TipoEmpresa,
    TipoOferta,
    Ubicacion,
    UnidadMedida,
    Usuario,
)
from app.repositories.material.material_sobrante_repository import MaterialSobranteRepository
from app.schemas.material_schema import FiltroMaterialRequest

BOGOTA = (4.65, -74.05)
SOACHA = (4.58, -74.22)  # ~20 km de Bogotá
MEDELLIN = (6.25, -75.56)  # ~240 km de Bogotá


def _empresa(db: Session, email: str, coordenadas: tuple[float, float]) -> Empresa:
    rol = db.query(Rol).filter_by(nombre="EMPRESA").one()
    usuario = Usuario(nombre=email, email=email, password_hash="x", rol=rol)
    empresa = Empresa(
        usuario=usuario,
        nombre=email,
        tipo=TipoEmpresa.MICROEMPRESA,
        ubicacion=Ubicacion(ciudad="X", latitud=coordenadas[0], longitud=coordenadas[1]),
    )
    db.add(empresa)
    db.flush()
    return empresa


def _material(db: Session, empresa: Empresa, titulo: str, **datos) -> MaterialSobrante:
    categoria = db.query(CategoriaMaterial).filter_by(codigo=datos.pop("categoria", "madera")).one()
    material = MaterialSobrante(
        empresa=empresa,
        categoria=categoria,
        titulo=titulo,
        cantidad=Decimal("10"),
        unidad_medida=UnidadMedida.UNIDAD,
        estado=datos.pop("estado", EstadoMaterial.BUENO),
        tipo_oferta=datos.pop("tipo_oferta", TipoOferta.VENTA),
        precio=datos.pop("precio", Decimal("1000")),
        disponibilidad=datos.pop("disponibilidad", DisponibilidadMaterial.DISPONIBLE),
        **datos,
    )
    db.add(material)
    db.flush()
    return material


def test_filtra_por_radio_y_ordena_por_cercania(db: Session) -> None:
    _material(db, _empresa(db, "med@x.co", MEDELLIN), "Medellín")
    _material(db, _empresa(db, "soa@x.co", SOACHA), "Soacha")
    _material(db, _empresa(db, "bog@x.co", BOGOTA), "Bogotá")
    repo = MaterialSobranteRepository(db)
    filtro = FiltroMaterialRequest(latitud=BOGOTA[0], longitud=BOGOTA[1], radio_km=50)

    cercanos, total = repo.buscar(filtro, offset=0, limite=10, orden="cercania")

    assert total == 2
    assert [m.titulo for m in cercanos] == ["Bogotá", "Soacha"]
    assert cercanos[0].distancia_km == 0
    assert 15 < cercanos[1].distancia_km < 25


def test_estado_minimo_precio_y_disponibilidad(db: Session) -> None:
    empresa = _empresa(db, "a@x.co", BOGOTA)
    _material(db, empresa, "Nuevo caro", estado=EstadoMaterial.NUEVO, precio=Decimal("9000"))
    _material(db, empresa, "Bueno barato", estado=EstadoMaterial.BUENO, precio=Decimal("500"))
    _material(db, empresa, "Deteriorado", estado=EstadoMaterial.DETERIORADO)
    _material(db, empresa, "Agotado", disponibilidad=DisponibilidadMaterial.AGOTADO)
    repo = MaterialSobranteRepository(db)

    buenos, _ = repo.buscar(
        FiltroMaterialRequest(estado_minimo=EstadoMaterial.BUENO),
        offset=0,
        limite=10,
        orden="precio",
    )
    baratos, _ = repo.buscar(
        FiltroMaterialRequest(precio_maximo=Decimal("1000")), offset=0, limite=10
    )

    assert [m.titulo for m in buenos] == ["Bueno barato", "Nuevo caro"]
    assert {m.titulo for m in baratos} == {"Bueno barato", "Deteriorado"}


def test_texto_categoria_y_exclusion_de_empresa(db: Session) -> None:
    propia = _empresa(db, "a@x.co", BOGOTA)
    otra = _empresa(db, "b@x.co", BOGOTA)
    _material(db, propia, "Retazos de pino")
    _material(db, otra, "Tablas de pino")
    _material(db, otra, "Lona gruesa", categoria="tela")
    repo = MaterialSobranteRepository(db)

    pino, _ = repo.buscar(
        FiltroMaterialRequest(texto="PINO"), offset=0, limite=10, excluir_empresa_id=propia.id
    )
    tela, total_tela = repo.buscar(
        FiltroMaterialRequest(categoria_codigo="tela"), offset=0, limite=10
    )

    assert [m.titulo for m in pino] == ["Tablas de pino"]
    assert total_tela == 1 and tela[0].titulo == "Lona gruesa"


def test_paginacion(db: Session) -> None:
    empresa = _empresa(db, "a@x.co", BOGOTA)
    for i in range(5):
        _material(db, empresa, f"M{i}")
    repo = MaterialSobranteRepository(db)

    pagina, total = repo.buscar(FiltroMaterialRequest(), offset=2, limite=2)

    assert total == 5
    assert len(pagina) == 2
