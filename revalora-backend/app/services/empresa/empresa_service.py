"""Lógica de negocio de empresas."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import AccesoDenegadoError, RecursoNoEncontradoError, ReglaNegocioError
from app.models import ActividadEconomica, Empresa, TipoEmpresa, Ubicacion, Usuario
from app.repositories.empresa.actividad_economica_repository import ActividadEconomicaRepository
from app.repositories.empresa.empresa_repository import EmpresaRepository
from app.schemas.empresa_schema import EmpresaRequest


class EmpresaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.empresas = EmpresaRepository(db)
        self.actividades = ActividadEconomicaRepository(db)

    def obtener(self, empresa_id: int) -> Empresa:
        empresa = self.empresas.obtener(empresa_id)
        if empresa is None:
            raise RecursoNoEncontradoError("Empresa no encontrada.")
        return empresa

    def buscar(
        self,
        *,
        texto: str | None,
        tipo: TipoEmpresa | None,
        ciudad: str | None,
        actividad_economica_id: int | None,
        offset: int,
        limite: int,
    ) -> tuple[Sequence[Empresa], int]:
        return self.empresas.buscar(
            texto=texto,
            tipo=tipo,
            ciudad=ciudad,
            actividad_economica_id=actividad_economica_id,
            offset=offset,
            limite=limite,
        )

    def listar_actividades(self) -> Sequence[ActividadEconomica]:
        return self.actividades.listar()

    def registrar(self, usuario: Usuario, datos: EmpresaRequest) -> Empresa:
        if usuario.empresa is not None:
            raise ReglaNegocioError("Tu cuenta ya tiene una empresa registrada.")
        self._validar(datos)

        empresa = Empresa(
            usuario=usuario,
            ubicacion=Ubicacion(**datos.ubicacion.model_dump()),
            **datos.model_dump(exclude={"ubicacion"}),
        )
        self.empresas.agregar(empresa)
        self.db.commit()
        return empresa

    def actualizar(self, usuario: Usuario, empresa_id: int, datos: EmpresaRequest) -> Empresa:
        empresa = self.obtener(empresa_id)
        if empresa.usuario_id != usuario.id and not usuario.es_admin:
            raise AccesoDenegadoError("Solo puedes modificar tu propia empresa.")
        self._validar(datos, empresa_id=empresa.id)

        for campo, valor in datos.model_dump(exclude={"ubicacion"}).items():
            setattr(empresa, campo, valor)
        for campo, valor in datos.ubicacion.model_dump().items():
            setattr(empresa.ubicacion, campo, valor)
        self.db.commit()
        return empresa

    def _validar(self, datos: EmpresaRequest, empresa_id: int | None = None) -> None:
        if datos.identificacion:
            existente = self.empresas.por_identificacion(datos.identificacion)
            if existente is not None and existente.id != empresa_id:
                raise ReglaNegocioError("Ya existe una empresa con esa identificación.")
        if datos.actividad_economica_id is not None and (
            self.actividades.obtener(datos.actividad_economica_id) is None
        ):
            raise RecursoNoEncontradoError("Actividad económica no encontrada.")
