"""Excepciones de negocio. Cada una define el código HTTP con el que se responde."""


class RevaloraError(Exception):
    """Error base de la aplicación."""

    estado_http: int = 500

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ArchivoInvalidoError(RevaloraError):
    estado_http = 400


class NoAutenticadoError(RevaloraError):
    """Falta el token de sesión o no es válido."""

    estado_http = 401


class AccesoDenegadoError(RevaloraError):
    """El usuario está autenticado pero no puede realizar la acción."""

    estado_http = 403


class DatosInvalidosError(RevaloraError):
    """Combinación de datos que no se puede validar solo con el esquema de entrada."""

    estado_http = 422


class RecursoNoEncontradoError(RevaloraError):
    estado_http = 404


class ReglaNegocioError(RevaloraError):
    estado_http = 409


class IaServiceError(RevaloraError):
    """El servicio de IA no respondió o devolvió un error."""

    estado_http = 502
