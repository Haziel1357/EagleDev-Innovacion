/* REVALORA · módulo coincidencia: lista de coincidencias entre ofertas y necesidades.
 *
 * RevaloraCoincidencia.panel(contenedor, { tipo, id }) carga y pinta las
 * coincidencias de uno de mis materiales (tipo "material": muestra necesidades
 * compatibles) o de una de mis necesidades (tipo "necesidad": muestra
 * materiales compatibles), con botón para recalcular.
 */

(function () {
    "use strict";

    const { $, html, pintar, formato, etiqueta, visualCategoria, avisar, conCarga, vacio } = Revalora;

    const CRITERIOS = [
        ["material", "Material"],
        ["cantidad", "Cantidad"],
        ["estado", "Estado"],
        ["dimensiones", "Medidas"],
        ["ubicacion", "Cercanía"],
        ["precio", "Precio"],
    ];

    function anillo(puntuacion) {
        const valor = Math.round(puntuacion);
        return html`<div class="puntuacion ${valor < 60 ? "puntuacion--media" : ""}" style="--valor:${valor}" title="Compatibilidad">
            <span>${valor}%</span>
        </div>`;
    }

    function criterios(detalle) {
        return html`<div class="criterios">${CRITERIOS.filter(([clave]) => clave in detalle).map(
            ([clave, texto]) => html`<span class="criterio">${texto}
                <span class="medidor ${detalle[clave] < 0.5 ? "medidor--bajo" : ""}"><span class="medidor__barra" style="width:${Math.round(detalle[clave] * 100)}%"></span></span>
            </span>`
        )}</div>`;
    }

    const distancia = (c) => (c.distancia_km != null ? ` · ${formato.distancia(c.distancia_km)}` : "");

    /** Coincidencia vista desde una necesidad: el protagonista es el material. */
    function conMaterial(c) {
        const m = c.material;
        const foto = m.fotos.find((f) => f.es_principal) || m.fotos[0];
        const [emoji, color] = visualCategoria(m.categoria.codigo);
        const precio = m.tipo_oferta === "APROVECHAMIENTO" ? "Gratis"
            : m.precio != null ? `${formato.moneda(m.precio)} / ${etiqueta("unidad_corta", m.unidad_medida)}` : etiqueta("tipo_oferta", m.tipo_oferta);
        return html`<a class="coincidencia" href="/app/materiales/${m.id}">
            <span class="coincidencia__imagen" style="--fondo-categoria:${color}">${foto ? html`<img src="${foto.url}" alt="">` : emoji}</span>
            <div class="coincidencia__info">
                <h3>${m.titulo}</h3>
                <span class="coincidencia__meta">${m.empresa.nombre} · 📍 ${m.empresa.ubicacion.ciudad}${distancia(c)}</span>
                <span class="texto-sm">${formato.cantidad(m.cantidad, m.unidad_medida)} · ${etiqueta("estado_material", m.estado)} · <strong>${precio}</strong></span>
                ${criterios(c.detalle)}
            </div>
            ${anillo(c.puntuacion)}
        </a>`;
    }

    /** Coincidencia vista desde un material: el protagonista es la necesidad. */
    function conNecesidad(c) {
        const n = c.necesidad;
        const [emoji, color] = visualCategoria(n.categoria.codigo);
        return html`<a class="coincidencia" href="/app/necesidades/${n.id}">
            <span class="coincidencia__imagen" style="--fondo-categoria:${color}">${emoji}</span>
            <div class="coincidencia__info">
                <h3>${n.titulo}</h3>
                <span class="coincidencia__meta">${n.empresa.nombre} · 📍 ${n.empresa.ubicacion.ciudad}${distancia(c)}</span>
                <span class="texto-sm">Necesita ${formato.cantidad(n.cantidad, n.unidad_medida)} · estado ${etiqueta("estado_material", n.estado_minimo).toLowerCase()} o mejor
                    ${n.presupuesto_maximo != null ? html` · <strong>hasta ${formato.moneda(n.presupuesto_maximo)}</strong>` : ""}</span>
                ${criterios(c.detalle)}
            </div>
            ${anillo(c.puntuacion)}
        </a>`;
    }

    async function panel(contenedor, { tipo, id }) {
        const esMaterial = tipo === "material";
        const cargar = () => (esMaterial ? Api.coincidencias.deMaterial(id, { tamano: 50 }) : Api.coincidencias.deNecesidad(id, { tamano: 50 }));
        const recalcular = () => (esMaterial ? Api.coincidencias.recalcularMaterial(id) : Api.coincidencias.recalcularNecesidad(id));

        function dibujar(coincidencias) {
            pintar(
                contenedor,
                html`<section class="coincidencias">
                    <div class="coincidencias__cabecera">
                        <div>
                            <h2>${esMaterial ? "Empresas que necesitan este material" : "Materiales que te sirven"}</h2>
                            <p class="texto-sm texto-secundario" style="margin:0">
                                ${coincidencias.length
                                    ? `${coincidencias.length} ${coincidencias.length === 1 ? "coincidencia" : "coincidencias"}, de la más a la menos compatible.`
                                    : "Calculadas según material, cantidad, estado, medidas, cercanía y precio."}
                            </p>
                        </div>
                        <button type="button" class="boton boton--secundario boton--sm" data-recalcular>Recalcular</button>
                    </div>
                    ${coincidencias.length
                        ? coincidencias.map(esMaterial ? conNecesidad : conMaterial)
                        : vacio({
                              icono: esMaterial ? "🔎" : "🌱",
                              titulo: "Aún no hay coincidencias",
                              mensaje: esMaterial
                                  ? "Cuando una empresa publique una necesidad compatible aparecerá aquí."
                                  : "Cuando alguien publique un sobrante compatible aparecerá aquí. También puedes buscar en el catálogo.",
                              accion: esMaterial ? "" : html`<a class="boton boton--secundario" href="/app/materiales">Explorar materiales</a>`,
                          })}
                </section>`
            );
            const boton = $("[data-recalcular]", contenedor);
            boton.addEventListener("click", () =>
                conCarga(boton, async () => {
                    try {
                        const nuevas = await recalcular();
                        dibujar(nuevas.sort((a, b) => b.puntuacion - a.puntuacion));
                        avisar("Coincidencias actualizadas.", "exito", 2500);
                    } catch (error) {
                        avisar(error.message, "error");
                    }
                })
            );
        }

        pintar(contenedor, html`<div class="cargando">Buscando coincidencias…</div>`);
        try {
            dibujar((await cargar()).elementos);
        } catch (error) {
            pintar(contenedor, html`<div class="alerta alerta--error"><p>${error.message}</p></div>`);
        }
    }

    /* ----------------------------------------- página: todas mis coincidencias */

    Revalora.pagina("coincidencias", () => {
        const contenedor = $("#coincidencias");
        const pestanas = [...document.querySelectorAll("#pestanas-coincidencias .pestana")];
        const miEmpresa = Revalora.sesion && Revalora.sesion.empresa_id;
        let lado = "";
        let datos = null;

        // Si el material es mío, lo interesante es la necesidad de la otra empresa (y al revés).
        const esDeMiMaterial = (c) => c.material.empresa.id === miEmpresa;

        function dibujar() {
            const visibles = datos.elementos.filter((c) =>
                lado === "materiales" ? esDeMiMaterial(c) : lado === "necesidades" ? !esDeMiMaterial(c) : true
            );
            if (!visibles.length) {
                pintar(contenedor, vacio({
                    icono: "🔗",
                    titulo: "Aún no hay coincidencias",
                    mensaje: "Publica materiales y necesidades: cruzamos automáticamente las de otras empresas con las tuyas.",
                    accion: html`<div class="fila" style="justify-content:center">
                        <a class="boton" href="/app/materiales/publicar">Publicar sobrante</a>
                        <a class="boton boton--secundario" href="/app/necesidades/publicar">Publicar necesidad</a></div>`,
                }));
                return;
            }
            pintar(contenedor, html`<div class="coincidencias">${visibles.map((c) => html`<div class="pila pila--sm">
                <span class="texto-xs texto-tenue">${esDeMiMaterial(c)
                    ? html`Tu material <strong>${c.material.titulo}</strong> le sirve a…`
                    : html`Para tu necesidad <strong>${c.necesidad.titulo}</strong>:`}</span>
                ${esDeMiMaterial(c) ? conNecesidad(c) : conMaterial(c)}
            </div>`)}</div>`);
        }

        async function cargar(pagina = 1) {
            try {
                datos = await Api.coincidencias.mias({ pagina, tamano: 30 });
            } catch (error) {
                pintar(contenedor, Revalora.errorCarga(error));
                return;
            }
            dibujar();
            Revalora.paginacion($("#paginacion"), datos, cargar);
        }

        pestanas.forEach((p) => p.addEventListener("click", () => {
            pestanas.forEach((x) => x.setAttribute("aria-selected", String(x === p)));
            lado = p.dataset.lado;
            if (datos) dibujar();
        }));
        cargar();
    });

    window.RevaloraCoincidencia = { panel, conMaterial, conNecesidad };
})();
