/* =============================================================================
   REVALORA · utilidades compartidas por todas las páginas
   - Revalora.sesion / Revalora.etiquetas: datos que inyecta la plantilla base.
   - html``: plantillas con escape automático de los valores interpolados.
   - Formato de moneda, cantidades y fechas.
   - Avisos flotantes, formularios (a JSON y errores por campo), paginación.
   - Navegación: menú móvil, menú de la cuenta y cierre de sesión.
   ========================================================================== */

(function () {
    "use strict";

    const datos = window.REVALORA || {};
    const etiquetas = datos.etiquetas || {};

    /* ------------------------------------------------------------ DOM y HTML */

    const $ = (selector, raiz = document) => raiz.querySelector(selector);
    const $$ = (selector, raiz = document) => [...raiz.querySelectorAll(selector)];

    class HtmlSeguro {
        constructor(texto) {
            this.texto = texto;
        }
        toString() {
            return this.texto;
        }
    }

    function escapar(valor) {
        return String(valor)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function aTexto(valor) {
        if (valor === null || valor === undefined || valor === false) return "";
        if (valor instanceof HtmlSeguro) return valor.texto;
        if (Array.isArray(valor)) return valor.map(aTexto).join("");
        return escapar(valor);
    }

    /** Plantilla HTML: escapa todo lo interpolado salvo otros html`` o crudo(). */
    function html(partes, ...valores) {
        let resultado = partes[0];
        valores.forEach((valor, i) => {
            resultado += aTexto(valor) + partes[i + 1];
        });
        return new HtmlSeguro(resultado);
    }

    const crudo = (texto) => new HtmlSeguro(texto);

    function pintar(elemento, contenido) {
        elemento.innerHTML = aTexto(contenido);
    }

    /* --------------------------------------------------------------- formato */

    const formatoNumero = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });
    const formatoMoneda = new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0,
    });
    const formatoFecha = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium" });
    const formatoFechaHora = new Intl.DateTimeFormat("es-CO", {
        dateStyle: "medium",
        timeStyle: "short",
    });
    const relativo = new Intl.RelativeTimeFormat("es", { numeric: "auto" });

    /** Las fechas sin zona horaria que envía la API están en UTC. */
    const aFecha = (iso) => new Date(/(Z|[+-]\d\d:?\d\d)$/i.test(iso) ? iso : `${iso}Z`);

    const formato = {
        numero: (n) => formatoNumero.format(Number(n)),
        moneda: (n) => formatoMoneda.format(Number(n)),
        cantidad: (n, unidad) => `${formatoNumero.format(Number(n))} ${etiqueta("unidad_corta", unidad)}`,
        fecha: (iso) => formatoFecha.format(aFecha(iso)),
        fechaHora: (iso) => formatoFechaHora.format(aFecha(iso)),
        distancia: (km) => (km < 1 ? `${Math.round(km * 1000)} m` : `${formatoNumero.format(km)} km`),
        porcentaje: (valor) => `${Math.round(valor * 100)} %`,
        haceCuanto(iso) {
            const segundos = (aFecha(iso) - Date.now()) / 1000;
            const tramos = [
                [60, "second"],
                [3600, "minute", 60],
                [86400, "hour", 3600],
                [2592000, "day", 86400],
                [31536000, "month", 2592000],
                [Infinity, "year", 31536000],
            ];
            const absoluto = Math.abs(segundos);
            for (const [limite, unidad, divisor = 1] of tramos) {
                if (absoluto < limite) return relativo.format(Math.round(segundos / divisor), unidad);
            }
            return "";
        },
        iniciales: (nombre) =>
            String(nombre || "?")
                .trim()
                .split(/\s+/)
                .slice(0, 2)
                .map((p) => p[0])
                .join("")
                .toUpperCase(),
    };

    function etiqueta(grupo, valor) {
        return (etiquetas[grupo] && etiquetas[grupo][valor]) || valor || "";
    }

    /* Emoji y color de cada categoría, para las imágenes de reemplazo. */
    const CATEGORIAS_VISUALES = {
        madera: ["🪵", "#ead7bf"],
        carton: ["📦", "#efdfc7"],
        plastico: ["🧴", "#d6e8f3"],
        tela: ["🧵", "#efdcec"],
        metal: ["🔩", "#dfe3e7"],
        vidrio: ["🫙", "#d5ecec"],
        papel: ["📄", "#f2ead2"],
        otro: ["♻️", "#e3f1e8"],
    };

    const visualCategoria = (codigo) => CATEGORIAS_VISUALES[codigo] || CATEGORIAS_VISUALES.otro;

    /* ---------------------------------------------------------------- avisos */

    const ICONOS_AVISO = {
        exito: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>',
        aviso: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/></svg>',
        info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
    };

    /** Muestra un aviso flotante y lo devuelve. Con duracion 0 queda hasta que se cierre. */
    function avisar(mensaje, tipo = "exito", duracion = 5000) {
        const contenedor = $("#avisos");
        if (!contenedor) return null;
        const aviso = document.createElement("div");
        aviso.className = `alerta alerta--${tipo} aviso`;
        aviso.setAttribute("role", tipo === "error" ? "alert" : "status");
        pintar(
            aviso,
            html`${crudo(ICONOS_AVISO[tipo] || "")}<p>${mensaje}</p><button type="button" class="aviso__cerrar" aria-label="Cerrar">×</button>`
        );
        const cerrar = () => aviso.remove();
        $(".aviso__cerrar", aviso).addEventListener("click", cerrar);
        contenedor.append(aviso);
        if (duracion) setTimeout(cerrar, duracion);
        return aviso;
    }

    const CLAVE_AVISO = "revalora:aviso";

    /** Guarda un aviso para mostrarlo en la siguiente página (tras redirigir). */
    function avisarAlCargar(mensaje, tipo = "exito") {
        try {
            sessionStorage.setItem(CLAVE_AVISO, JSON.stringify({ mensaje, tipo }));
        } catch {
            /* sin almacenamiento: el aviso simplemente no se muestra */
        }
    }

    function mostrarAvisoPendiente() {
        try {
            const guardado = sessionStorage.getItem(CLAVE_AVISO);
            if (!guardado) return;
            sessionStorage.removeItem(CLAVE_AVISO);
            const { mensaje, tipo } = JSON.parse(guardado);
            avisar(mensaje, tipo);
        } catch {
            /* ignorado */
        }
    }

    function irA(url, mensaje, tipo) {
        if (mensaje) avisarAlCargar(mensaje, tipo);
        window.location.href = url;
    }

    /* ----------------------------------------------------------- formularios */

    /** Convierte un formulario a objeto. Los nombres con punto crean objetos anidados
     *  ("ubicacion.ciudad"); los campos vacíos se omiten salvo data-enviar-vacio. */
    function formularioAObjeto(formulario) {
        const resultado = {};
        for (const campo of formulario.elements) {
            if (!campo.name || campo.disabled || campo.type === "file") continue;
            if (campo.type === "radio" && !campo.checked) continue;

            let valor;
            if (campo.type === "checkbox") valor = campo.checked;
            else if (campo.value.trim() === "") {
                if (!("enviarVacio" in campo.dataset)) continue;
                valor = null;
            } else if (campo.type === "number") valor = Number(campo.value);
            else valor = campo.value.trim();

            const partes = campo.name.split(".");
            let nivel = resultado;
            partes.slice(0, -1).forEach((parte) => {
                nivel[parte] = nivel[parte] || {};
                nivel = nivel[parte];
            });
            nivel[partes.at(-1)] = valor;
        }
        return resultado;
    }

    /** Rellena un formulario a partir de un objeto (acepta nombres con punto). */
    function rellenarFormulario(formulario, objeto) {
        for (const campo of formulario.elements) {
            if (!campo.name || campo.type === "file") continue;
            const valor = campo.name.split(".").reduce((o, k) => (o == null ? o : o[k]), objeto);
            if (valor === undefined) continue;
            if (campo.type === "checkbox") campo.checked = Boolean(valor);
            else if (campo.type === "radio") campo.checked = String(valor) === campo.value;
            // Los Decimal llegan como texto ("15.000"): se normalizan a 15.
            else if (campo.type === "number" && valor !== null && valor !== "") campo.value = Number(valor);
            else campo.value = valor ?? "";
        }
    }

    const TRADUCCIONES = [
        [/^Field required$/, () => "Este campo es obligatorio."],
        [/^String should have at least (\d+) characters?$/, (m) => `Debe tener al menos ${m[1]} caracteres.`],
        [/^String should have at most (\d+) characters?$/, (m) => `Debe tener como máximo ${m[1]} caracteres.`],
        [/^Input should be greater than (\S+)$/, (m) => `Debe ser mayor que ${m[1]}.`],
        [/^Input should be greater than or equal to (\S+)$/, (m) => `Debe ser mayor o igual a ${m[1]}.`],
        [/^Input should be less than or equal to (\S+)$/, (m) => `Debe ser menor o igual a ${m[1]}.`],
        [/^value is not a valid email address/i, () => "Escribe un correo electrónico válido."],
        [/^Input should be a valid (number|integer|decimal)/, () => "Escribe un número válido."],
        [/^Decimal input should have no more than (\d+) decimal places?$/, (m) => `Usa como máximo ${m[1]} decimales.`],
        [/^Value error, (.*)$/, (m) => m[1]],
    ];

    function traducir(mensaje) {
        for (const [patron, traduccion] of TRADUCCIONES) {
            const coincidencia = String(mensaje).match(patron);
            if (coincidencia) return traduccion(coincidencia);
        }
        return mensaje;
    }

    function limpiarErrores(formulario) {
        $$(".campo--invalido", formulario).forEach((c) => c.classList.remove("campo--invalido"));
        $$(".campo__error", formulario).forEach((e) => e.remove());
        const general = $(".formulario__error", formulario);
        if (general) general.hidden = true;
    }

    function marcarCampo(formulario, nombre, mensaje) {
        const entrada = formulario.querySelector(`[name="${CSS.escape(nombre)}"]`);
        const campo = entrada && entrada.closest(".campo");
        if (!campo) return false;
        campo.classList.add("campo--invalido");
        const error = document.createElement("p");
        error.className = "campo__error";
        error.textContent = mensaje;
        campo.append(error);
        return true;
    }

    /** Muestra el error de la API: por campo cuando es de validación (422) y,
     *  si no corresponde a ningún campo, en el recuadro general del formulario. */
    function mostrarErrores(formulario, error) {
        limpiarErrores(formulario);
        const generales = [];
        for (const detalle of error.detalles || []) {
            const nombre = String(detalle.campo || "").replace(/^(body|query|path)\.?/, "");
            const mensaje = traducir(detalle.mensaje);
            if (!nombre || !marcarCampo(formulario, nombre, mensaje)) generales.push(mensaje);
        }
        if (!error.detalles || !error.detalles.length) generales.push(error.message);

        const recuadro = $(".formulario__error", formulario);
        if (generales.length && recuadro) {
            pintar(recuadro, html`${crudo(ICONOS_AVISO.error)}<p>${generales.join(" ")}</p>`);
            recuadro.hidden = false;
            recuadro.scrollIntoView({ block: "nearest", behavior: "smooth" });
        } else if (generales.length) {
            avisar(generales.join(" "), "error");
        } else {
            const primero = $(".campo--invalido input, .campo--invalido select, .campo--invalido textarea", formulario);
            if (primero) primero.focus();
        }
    }

    /** Ejecuta una acción mostrando el botón como ocupado mientras dura. */
    async function conCarga(boton, accion) {
        if (!boton) return accion();
        boton.setAttribute("aria-busy", "true");
        boton.disabled = true;
        try {
            return await accion();
        } finally {
            boton.removeAttribute("aria-busy");
            boton.disabled = false;
        }
    }

    /** Envía un formulario con la función dada y gestiona carga y errores.
     *  `enviar` recibe el objeto del formulario y devuelve una promesa. */
    function manejarFormulario(formulario, enviar) {
        formulario.addEventListener("submit", async (evento) => {
            evento.preventDefault();
            limpiarErrores(formulario);
            const boton = evento.submitter || $('[type="submit"]', formulario);
            try {
                await conCarga(boton, () => enviar(formularioAObjeto(formulario), formulario));
            } catch (error) {
                if (error instanceof Api.ApiError) mostrarErrores(formulario, error);
                else {
                    console.error(error);
                    avisar("Ocurrió un error inesperado.", "error");
                }
            }
        });
    }

    /* ------------------------------------------------------------- diálogos */

    /** Pide confirmación con un <dialog>. Devuelve una promesa con true/false. */
    function confirmar({ titulo, mensaje, aceptar = "Confirmar", peligro = false }) {
        return new Promise((resolver) => {
            const dialogo = document.createElement("dialog");
            dialogo.className = "dialogo";
            pintar(
                dialogo,
                html`<form method="dialog">
                    <div class="dialogo__cuerpo"><h2>${titulo}</h2><p class="texto-secundario">${mensaje}</p></div>
                    <div class="dialogo__acciones">
                        <button class="boton boton--secundario" value="no">Cancelar</button>
                        <button class="boton ${peligro ? "boton--peligro" : ""}" value="si">${aceptar}</button>
                    </div>
                </form>`
            );
            dialogo.addEventListener("close", () => {
                resolver(dialogo.returnValue === "si");
                dialogo.remove();
            });
            document.body.append(dialogo);
            dialogo.showModal();
        });
    }

    /* ----------------------------------------------------------- paginación */

    function paginacion(contenedor, { pagina, tamano, total }, alCambiar) {
        const paginas = Math.max(1, Math.ceil(total / tamano));
        if (paginas <= 1) {
            contenedor.innerHTML = "";
            return;
        }
        pintar(
            contenedor,
            html`<button type="button" class="boton boton--secundario boton--sm" data-pagina="${pagina - 1}" ${pagina <= 1 ? crudo("disabled") : ""}>← Anterior</button>
                <span class="paginacion__info">Página ${pagina} de ${paginas}</span>
                <button type="button" class="boton boton--secundario boton--sm" data-pagina="${pagina + 1}" ${pagina >= paginas ? crudo("disabled") : ""}>Siguiente →</button>`
        );
        $$("[data-pagina]", contenedor).forEach((boton) =>
            boton.addEventListener("click", () => alCambiar(Number(boton.dataset.pagina)))
        );
    }

    /* --------------------------------------------------------- estados vacíos */

    function vacio({ icono = "🔍", titulo, mensaje = "", accion = "" }) {
        return html`<div class="vacio">
            <div class="vacio__icono" aria-hidden="true">${icono}</div>
            <h3>${titulo}</h3>
            ${mensaje ? html`<p>${mensaje}</p>` : ""}
            ${accion}
        </div>`;
    }

    function errorCarga(error) {
        return vacio({
            icono: "⚠️",
            titulo: "No pudimos cargar la información",
            mensaje: error.message,
            accion: html`<button type="button" class="boton boton--secundario" onclick="location.reload()">Reintentar</button>`,
        });
    }

    /* ----------------------------------------------------------- geolocalización */

    function obtenerUbicacion() {
        return new Promise((resolver, rechazar) => {
            if (!navigator.geolocation) {
                rechazar(new Error("Tu navegador no permite obtener la ubicación."));
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (posicion) =>
                    resolver({
                        latitud: Number(posicion.coords.latitude.toFixed(6)),
                        longitud: Number(posicion.coords.longitude.toFixed(6)),
                    }),
                () => rechazar(new Error("No se pudo obtener tu ubicación. Revisa los permisos del navegador.")),
                { timeout: 10000 }
            );
        });
    }

    /* ------------------------------------------------------------ navegación */

    function iniciarNavegacion() {
        const alternar = $(".nav__alternar");
        const nav = $("#nav-principal");
        if (alternar && nav) {
            alternar.addEventListener("click", () => {
                const abierto = nav.classList.toggle("abierto");
                alternar.setAttribute("aria-expanded", String(abierto));
            });
        }

        const botonCuenta = $(".menu-cuenta__boton");
        const panelCuenta = $(".menu-cuenta__panel");
        if (botonCuenta && panelCuenta) {
            const cerrar = () => {
                panelCuenta.hidden = true;
                botonCuenta.setAttribute("aria-expanded", "false");
            };
            botonCuenta.addEventListener("click", (evento) => {
                evento.stopPropagation();
                const abrir = panelCuenta.hidden;
                panelCuenta.hidden = !abrir;
                botonCuenta.setAttribute("aria-expanded", String(abrir));
            });
            document.addEventListener("click", (evento) => {
                if (!panelCuenta.contains(evento.target)) cerrar();
            });
            document.addEventListener("keydown", (evento) => {
                if (evento.key === "Escape") cerrar();
            });
        }

        $$("[data-cerrar-sesion]").forEach((boton) =>
            boton.addEventListener("click", async () => {
                try {
                    await Api.auth.logout();
                } finally {
                    irA("/", "Cerraste sesión.", "info");
                }
            })
        );

        // Solicitudes recibidas que esperan respuesta.
        const contador = $("[data-contador-solicitudes]");
        if (contador) {
            Api.get("/solicitudes/recibidas", { estado: "PENDIENTE", tamano: 1 })
                .then(({ total }) => {
                    contador.textContent = total > 99 ? "99+" : total;
                    contador.hidden = total === 0;
                    contador.setAttribute("aria-label", `${total} pendientes`);
                })
                .catch(() => {});
        }

        // Marca el enlace de la sección actual.
        const ruta = window.location.pathname;
        $$(".nav__enlace[href]").forEach((enlace) => {
            const destino = enlace.getAttribute("href");
            if (destino !== "/" && (ruta === destino || ruta.startsWith(`${destino}/`))) {
                enlace.setAttribute("aria-current", "page");
            }
        });
    }

    /* -------------------------------------------------------- páginas (init) */

    const paginas = {};

    /** Registra la función de arranque de una página (data-pagina del <body>). */
    function pagina(nombre, iniciar) {
        paginas[nombre] = iniciar;
    }

    function arrancar() {
        iniciarNavegacion();
        mostrarAvisoPendiente();
        const nombre = document.body.dataset.pagina;
        if (nombre && paginas[nombre]) {
            Promise.resolve(paginas[nombre](document.body.dataset)).catch((error) => {
                console.error(error);
                avisar(error.message || "Ocurrió un error inesperado.", "error");
            });
        }
    }

    document.addEventListener("DOMContentLoaded", arrancar);

    /** Parámetros de la URL actual como objeto. */
    const parametrosUrl = () => Object.fromEntries(new URLSearchParams(window.location.search));

    /** URL interna segura para redirigir tras iniciar sesión (evita redirecciones abiertas). */
    function rutaSegura(ruta, porDefecto) {
        return typeof ruta === "string" && ruta.startsWith("/") && !ruta.startsWith("//") ? ruta : porDefecto;
    }

    window.Revalora = {
        sesion: datos.sesion || null,
        etiquetas,
        solicitudPorOferta: datos.solicitudPorOferta || {},
        tamanoMaximoMb: datos.tamanoMaximoMb || 5,
        $,
        $$,
        html,
        crudo,
        pintar,
        escapar,
        formato,
        etiqueta,
        visualCategoria,
        avisar,
        avisarAlCargar,
        irA,
        formularioAObjeto,
        rellenarFormulario,
        limpiarErrores,
        mostrarErrores,
        manejarFormulario,
        conCarga,
        confirmar,
        paginacion,
        vacio,
        errorCarga,
        obtenerUbicacion,
        parametrosUrl,
        rutaSegura,
        pagina,
    };
})();
