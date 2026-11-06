"""GET /api/v1/salud: verificación de que el servicio está activo."""

from fastapi import APIRouter

from app.api.dependencias import ProveedorDep

router = APIRouter(tags=["Salud"])


@router.get("/salud")
def salud(proveedor: ProveedorDep) -> dict[str, str]:
    """`modelo_vision` indica qué clasificador está en uso: `clip`, `heuristico`
    o `sin_cargar` (se cargará con la primera foto)."""
    return {"estado": "ok", "modelo_vision": proveedor.nombre}
