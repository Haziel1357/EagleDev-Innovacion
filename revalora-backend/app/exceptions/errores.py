"""Excepciones de negocio. Cada una define el código HTTP con el que se responde."""


class RevaloraError(Exception):
    """Error base de la aplicación."""

    estado_http: int = 500

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class RecursoNoEncontradoError(RevaloraError):
    estado_http = 404


class ReglaNegocioError(RevaloraError):
    estado_http = 409


class ArchivoInvalidoError(RevaloraError):
    estado_http = 400


class IaServiceError(RevaloraError):
    """El servicio de IA no respondió o devolvió un error."""

    estado_http = 502
