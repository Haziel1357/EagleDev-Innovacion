"""Oportunidades productivas: sugiere productos y detecta los materiales que faltan.

Se envían a la IA los materiales que la empresa tiene disponibles (o los que indique)
y por cada material faltante se cuenta cuántas publicaciones hay en la plataforma,
para que la empresa sepa si puede conseguirlo aquí.
"""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import AccesoDenegadoError, RecursoNoEncontradoError, ReglaNegocioError
from app.models import Empresa, MaterialFaltante, OportunidadProductiva, ProductoSugerido
from app.repositories.material.categoria_material_repository import CategoriaMaterialRepository
from app.repositories.material.material_sobrante_repository import MaterialSobranteRepository
from app.repositories.oportunidad.oportunidad_productiva_repository import (
    OportunidadProductivaRepository,
)
from app.schemas.oportunidad_schema import AnalisisOportunidadRequest
from app.services.ia.ia_service_client import IaServiceClient


class OportunidadProductivaService:
    def __init__(self, db: Session, ia: IaServiceClient) -> None:
        self.db = db
        self.ia = ia
        self.oportunidades = OportunidadProductivaRepository(db)
        self.categorias = CategoriaMaterialRepository(db)
        self.materiales = MaterialSobranteRepository(db)

    def analizar(
        self, empresa: Empresa, datos: AnalisisOportunidadRequest
    ) -> OportunidadProductiva:
        codigos = self._materiales_a_analizar(empresa, datos.categoria_ids)
        respuesta = self.ia.sugerir_oportunidades(codigos, datos.max_productos)

        faltantes_codigos = {
            f.material.strip().lower() for p in respuesta.productos for f in p.materiales_faltantes
        }
        categorias = self.categorias.por_codigos(faltantes_codigos)
        disponibles = {
            codigo: self.materiales.contar_disponibles_por_categoria(categoria.id)
            for codigo, categoria in categorias.items()
        }

        oportunidad = OportunidadProductiva(
            empresa_id=empresa.id,
            materiales_analizados=codigos,
            productos=[
                ProductoSugerido(
                    nombre=producto.nombre,
                    descripcion=producto.descripcion,
                    viabilidad=producto.viabilidad,
                    materiales_utilizados=[
                        m.strip().lower() for m in producto.materiales_utilizados
                    ],
                    materiales_faltantes=[
                        MaterialFaltante(
                            material=(codigo := faltante.material.strip().lower()),
                            categoria=categorias.get(codigo),
                            descripcion=faltante.descripcion,
                            disponibles_en_plataforma=disponibles.get(codigo, 0),
                        )
                        for faltante in producto.materiales_faltantes
                    ],
                )
                for producto in respuesta.productos[: datos.max_productos]
            ],
        )
        self.oportunidades.agregar(oportunidad)
        self.db.commit()
        self.db.refresh(oportunidad)
        return oportunidad

    def de_empresa(
        self, empresa: Empresa, offset: int, limite: int
    ) -> tuple[Sequence[OportunidadProductiva], int]:
        return self.oportunidades.de_empresa(empresa.id, offset, limite)

    def obtener(self, empresa: Empresa, oportunidad_id: int) -> OportunidadProductiva:
        oportunidad = self.oportunidades.obtener(oportunidad_id)
        if oportunidad is None:
            raise RecursoNoEncontradoError("Oportunidad no encontrada.")
        if oportunidad.empresa_id != empresa.id:
            raise AccesoDenegadoError("Esta oportunidad no pertenece a tu empresa.")
        return oportunidad

    def _materiales_a_analizar(
        self, empresa: Empresa, categoria_ids: list[int] | None
    ) -> list[str]:
        if categoria_ids:
            categorias = self.categorias.por_ids(categoria_ids)
            if len(categorias) != len(set(categoria_ids)):
                raise RecursoNoEncontradoError("Alguna de las categorías indicadas no existe.")
            return sorted(c.codigo for c in categorias)

        propios = self.materiales.disponibles_de_empresa(empresa.id)
        if not propios:
            raise ReglaNegocioError(
                "Tu empresa no tiene materiales disponibles publicados. "
                "Publica alguno o indica las categorías a analizar."
            )
        return sorted({m.categoria.codigo for m in propios})
