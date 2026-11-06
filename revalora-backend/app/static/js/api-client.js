/* =============================================================================
   REVALORA · cliente de la API REST
   Envía las peticiones con la cookie de sesión (no hace falta manejar el token
   en JavaScript). Los errores llegan como ApiError con el formato ErrorResponse
   del backend: { estado, error, mensaje, ruta, detalles? }.
   ========================================================================== */

(function () {
    "use strict";

    class ApiError extends Error {
        constructor(estado, cuerpo) {
            super((cuerpo && cuerpo.mensaje) || "No se pudo completar la operación.");
            this.name = "ApiError";
            this.estado = estado;
            this.detalles = (cuerpo && cuerpo.detalles) || [];
        }

        get esNoAutenticado() {
            return this.estado === 401;
        }
    }

    function construirUrl(ruta, params) {
        if (!params) return ruta;
        const consulta = new URLSearchParams();
        for (const [clave, valor] of Object.entries(params)) {
            if (valor === undefined || valor === null || valor === "") continue;
            if (Array.isArray(valor)) valor.forEach((v) => consulta.append(clave, v));
            else consulta.append(clave, valor);
        }
        const texto = consulta.toString();
        return texto ? `${ruta}?${texto}` : ruta;
    }

    async function solicitar(metodo, ruta, { params, json, formData } = {}) {
        const opciones = {
            method: metodo,
            credentials: "same-origin",
            headers: { Accept: "application/json" },
        };
        if (json !== undefined) {
            opciones.headers["Content-Type"] = "application/json";
            opciones.body = JSON.stringify(json);
        } else if (formData) {
            opciones.body = formData;
        }

        let respuesta;
        try {
            respuesta = await fetch(construirUrl(ruta, params), opciones);
        } catch {
            throw new ApiError(0, { mensaje: "No se pudo conectar con el servidor." });
        }

        if (respuesta.status === 204) return null;
        const esJson = (respuesta.headers.get("content-type") || "").includes("json");
        const cuerpo = esJson ? await respuesta.json().catch(() => null) : null;
        if (!respuesta.ok) throw new ApiError(respuesta.status, cuerpo);
        return cuerpo;
    }

    const http = {
        get: (ruta, params) => solicitar("GET", ruta, { params }),
        post: (ruta, json) => solicitar("POST", ruta, { json }),
        put: (ruta, json) => solicitar("PUT", ruta, { json }),
        patch: (ruta, json) => solicitar("PATCH", ruta, { json }),
        eliminar: (ruta) => solicitar("DELETE", ruta),
        subir: (ruta, formData) => solicitar("POST", ruta, { formData }),
    };

    /* Endpoints agrupados por módulo (mismo orden que app/controllers). */
    window.Api = {
        ApiError,
        ...http,

        auth: {
            registro: (datos) => http.post("/auth/registro", datos),
            login: (datos) => http.post("/auth/login", datos),
            logout: () => http.post("/auth/logout"),
        },
        usuarios: {
            yo: () => http.get("/usuarios/me"),
            actualizarme: (datos) => http.put("/usuarios/me", datos),
        },
        empresas: {
            actividades: () => http.get("/empresas/actividades"),
            mia: () => http.get("/empresas/mia"),
            obtener: (id) => http.get(`/empresas/${id}`),
            registrar: (datos) => http.post("/empresas", datos),
            actualizar: (id, datos) => http.put(`/empresas/${id}`, datos),
        },
        categorias: {
            listar: () => http.get("/categorias"),
        },
        materiales: {
            listar: (params) => http.get("/materiales", params),
            mios: (params) => http.get("/materiales/mios", params),
            obtener: (id) => http.get(`/materiales/${id}`),
            publicar: (datos) => http.post("/materiales", datos),
            actualizar: (id, datos) => http.put(`/materiales/${id}`, datos),
            disponibilidad: (id, disponibilidad) =>
                http.patch(`/materiales/${id}/disponibilidad`, { disponibilidad }),
            retirar: (id) => http.eliminar(`/materiales/${id}`),
            subirFotos: (id, archivos) => {
                const datos = new FormData();
                [...archivos].forEach((archivo) => datos.append("fotos", archivo));
                return http.subir(`/materiales/${id}/fotos`, datos);
            },
            fotoPrincipal: (id, fotoId) => http.patch(`/materiales/${id}/fotos/${fotoId}/principal`),
            eliminarFoto: (id, fotoId) => http.eliminar(`/materiales/${id}/fotos/${fotoId}`),
        },
        buscador: {
            tradicional: (params) => http.get("/buscador/tradicional", params),
            inteligente: (datos) => http.post("/buscador/inteligente", datos),
            historial: (params) => http.get("/buscador/inteligente/historial", params),
            busqueda: (id) => http.get(`/buscador/inteligente/historial/${id}`),
        },
        oportunidades: {
            analizar: (datos) => http.post("/oportunidades/analizar", datos),
            listar: (params) => http.get("/oportunidades", params),
            obtener: (id) => http.get(`/oportunidades/${id}`),
        },
        ia: {
            reconocer: (imagen) => {
                const datos = new FormData();
                datos.append("imagen", imagen);
                return http.subir("/ia/reconocimiento", datos);
            },
        },
        necesidades: {
            listar: (params) => http.get("/necesidades", params),
            mias: (params) => http.get("/necesidades/mias", params),
            obtener: (id) => http.get(`/necesidades/${id}`),
            publicar: (datos) => http.post("/necesidades", datos),
            actualizar: (id, datos) => http.put(`/necesidades/${id}`, datos),
            estado: (id, estado) => http.patch(`/necesidades/${id}/estado`, { estado }),
            cerrar: (id) => http.eliminar(`/necesidades/${id}`),
        },
        coincidencias: {
            mias: (params) => http.get("/coincidencias", params),
            deMaterial: (id, params) => http.get(`/coincidencias/materiales/${id}`, params),
            deNecesidad: (id, params) => http.get(`/coincidencias/necesidades/${id}`, params),
            recalcularMaterial: (id) => http.post(`/coincidencias/materiales/${id}/recalcular`),
            recalcularNecesidad: (id) => http.post(`/coincidencias/necesidades/${id}/recalcular`),
        },
        solicitudes: {
            crear: (datos) => http.post("/solicitudes", datos),
            recibidas: (params) => http.get("/solicitudes/recibidas", params),
            enviadas: (params) => http.get("/solicitudes/enviadas", params),
            obtener: (id) => http.get(`/solicitudes/${id}`),
            /** accion: aceptar | rechazar | cancelar | completar */
            responder: (id, accion, comentario) =>
                http.post(`/solicitudes/${id}/${accion}`, comentario ? { comentario } : undefined),
        },
        historial: {
            listar: (params) => http.get("/historial", params),
        },
    };
})();
