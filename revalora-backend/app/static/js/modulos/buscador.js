/* REVALORA · módulo buscador: buscador inteligente por producto a fabricar.
 * POST /buscador/inteligente devuelve los materiales que la IA cree necesarios y,
 * por cada uno, los sobrantes disponibles ordenados por ajuste (0-100). */

(function () {
    "use strict";

    const R = Revalora;
    const { $, $$, html, pintar, formato, etiqueta, visualCategoria, avisar, vacio, errorCarga } = R;

    const nombreRequerido = (r) => (r.categoria ? r.categoria.nombre : r.material);

    function cabeceraRequerido(r, extra = "") {
        const [emoji, color] = visualCategoria(r.categoria ? r.categoria.codigo : "otro");
        const cantidad = r.cantidad_estimada != null
            ? ` · aprox. ${formato.numero(r.cantidad_estimada)} ${r.unidad_medida ? etiqueta("unidad_corta", r.unidad_medida) : ""}`
            : "";
        return html`<div class="requerido__cabecera">
            <span class="requerido__emoji" style="background:${color}" aria-hidden="true">${emoji}</span>
            <div>
                <h2>${nombreRequerido(r)}</h2>
                <p>${r.funcion ? `Función: ${r.funcion}` : "Material necesario"}${cantidad}</p>
            </div>
            ${extra}
        </div>`;
    }

    function sinResultados(r) {
        if (!r.categoria) {
            return html`<div class="sin-resultados"><span>“${r.material}” no corresponde a ninguna categoría de la plataforma; tendrás que conseguirlo por fuera.</span></div>`;
        }
        return html`<div class="sin-resultados">
            <span>Por ahora nadie ofrece ${r.categoria.nombre.toLowerCase()}. Publica una necesidad y te avisaremos con las coincidencias.</span>
            ${R.sesion && R.sesion.empresa_id ? html`<a class="boton boton--secundario boton--sm" href="/necesidades/publicar?categoria_id=${r.categoria.id}">Publicar necesidad</a>` : ""}
        </div>`;
    }

    function pintarResultado(contenedor, resultado) {
        const requeridos = resultado.materiales_requeridos;
        pintar(
            contenedor,
            html`<div class="interpretacion">
                <span>Para fabricar <strong>${resultado.producto_interpretado || resultado.descripcion}</strong> necesitas:</span>
                <div class="materiales-requeridos">${requeridos.map((r) => html`<span class="etiqueta">${visualCategoria(r.categoria ? r.categoria.codigo : "otro")[0]} ${nombreRequerido(r)}</span>`)}</div>
            </div>
            ${requeridos.length
                ? requeridos.map((r) => html`<section class="requerido">
                    ${cabeceraRequerido(r, r.categoria && r.resultados.length ? html`<a href="/materiales?categoria_id=${r.categoria.id}">Ver todos →</a>` : "")}
                    ${r.resultados.length
                        ? html`<div class="rejilla-materiales">${r.resultados.map((rec) => html`<div class="recomendado">
                            <span class="recomendado__ajuste" title="Qué tan bien se ajusta a tu búsqueda">${Math.round(rec.puntuacion)}% ajuste</span>
                            ${RevaloraMaterial.tarjetaMaterial(rec.material)}
                        </div>`)}</div>`
                        : sinResultados(r)}
                </section>`)
                : vacio({ icono: "🤔", titulo: "La IA no identificó materiales", mensaje: "Intenta describir el producto con más detalle." })}`
        );
    }

    /** Búsqueda guardada: el historial conserva los materiales, no los resultados. */
    function pintarGuardada(contenedor, busqueda, repetir) {
        pintar(
            contenedor,
            html`<div class="interpretacion">
                <span>Buscaste <strong>“${busqueda.descripcion}”</strong> el ${formato.fechaHora(busqueda.creado_en)}</span>
                <div class="materiales-requeridos"><button type="button" class="boton boton--sm" data-repetir>Repetir búsqueda</button></div>
            </div>
            ${busqueda.materiales_requeridos.map((r) => html`<section class="requerido">
                ${cabeceraRequerido(r, r.categoria ? html`<a href="/materiales?categoria_id=${r.categoria.id}">Ver disponibles →</a>` : "")}
            </section>`)}`
        );
        $("[data-repetir]", contenedor).addEventListener("click", () => repetir(busqueda.descripcion));
    }

    R.pagina("buscador", () => {
        const formulario = $("#formulario-buscador");
        const resultados = $("#resultados-buscador");
        const historial = $("#historial-buscador");
        const campo = $("#descripcion");

        async function cargarHistorial(actual) {
            try {
                const datos = await Api.buscador.historial({ tamano: 10 });
                if (!datos.elementos.length) {
                    pintar(historial, html`<p class="texto-sm texto-tenue">Tus búsquedas aparecerán aquí.</p>`);
                    return;
                }
                pintar(
                    historial,
                    html`<ul class="historial-busquedas">${datos.elementos.map((b) => html`<li>
                        <button type="button" data-busqueda="${b.id}" aria-current="${b.id === actual}">
                            <strong>${b.descripcion}</strong>
                            <span>${formato.haceCuanto(b.creado_en)} · ${b.materiales_requeridos.length} materiales</span>
                        </button>
                    </li>`)}</ul>`
                );
                $$("[data-busqueda]", historial).forEach((boton) =>
                    boton.addEventListener("click", async () => {
                        $$("[data-busqueda]", historial).forEach((b) => b.setAttribute("aria-current", String(b === boton)));
                        try {
                            pintarGuardada(resultados, await Api.buscador.busqueda(boton.dataset.busqueda), buscarTexto);
                            resultados.scrollIntoView({ behavior: "smooth", block: "start" });
                        } catch (error) {
                            avisar(error.message, "error");
                        }
                    })
                );
            } catch (error) {
                pintar(historial, html`<p class="texto-sm texto-tenue">${error.message}</p>`);
            }
        }

        function buscarTexto(texto) {
            campo.value = texto;
            formulario.requestSubmit();
            window.scrollTo({ top: 0, behavior: "smooth" });
        }

        $$("#ejemplos .chip").forEach((chip) => chip.addEventListener("click", () => buscarTexto(`Quiero fabricar ${chip.textContent.toLowerCase()}`)));
        campo.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                formulario.requestSubmit();
            }
        });

        const botonUbicacion = $("#usar-ubicacion");
        if (botonUbicacion) {
            botonUbicacion.addEventListener("click", () =>
                R.conCarga(botonUbicacion, async () => {
                    try {
                        const { latitud, longitud } = await R.obtenerUbicacion();
                        formulario.elements.latitud.value = latitud;
                        formulario.elements.longitud.value = longitud;
                        botonUbicacion.textContent = "✔ Ubicación agregada";
                    } catch (error) {
                        avisar(error.message, "aviso");
                    }
                })
            );
        }

        R.manejarFormulario(formulario, async (datos) => {
            const anterior = resultados.innerHTML;
            pintar(resultados, html`<div class="cargando">La IA está analizando qué materiales necesitas…</div>`);
            try {
                const resultado = await Api.buscador.inteligente(datos);
                pintarResultado(resultados, resultado);
                cargarHistorial(resultado.busqueda_id);
            } catch (error) {
                if (error.estado === 422) {
                    resultados.innerHTML = anterior;
                    throw error; // se muestra junto al campo
                }
                pintar(resultados, error.estado === 502
                    ? vacio({ icono: "🤖", titulo: "El servicio de IA no está disponible", mensaje: `${error.message} Mientras tanto, puedes buscar por categoría en el catálogo.`, accion: html`<a class="boton boton--secundario" href="/materiales">Ir al catálogo</a>` })
                    : errorCarga(error));
            }
        });

        const inicial = R.parametrosUrl().q;
        if (inicial) buscarTexto(inicial);
        cargarHistorial();
    });
})();
