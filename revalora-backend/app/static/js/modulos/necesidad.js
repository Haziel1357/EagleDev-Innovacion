/* REVALORA · módulo necesidad: lista pública, detalle (con coincidencias para
 * la empresa dueña), publicación/edición y "mis necesidades". */

(function () {
    "use strict";

    const R = Revalora;
    const { $, $$, html, crudo, pintar, formato, etiqueta, visualCategoria, avisar, irA, vacio, errorCarga } = R;

    const ICONO_EDITAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>';
    const ICONO_X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>';

    const insigniaEstado = (estado) =>
        html`<span class="etiqueta estado-necesidad-${estado}"><span class="punto"></span> ${etiqueta("estado_necesidad", estado)}</span>`;

    function textoDimensiones(d) {
        const medidas = [d.largo_cm, d.ancho_cm, d.alto_cm].filter((v) => v != null);
        return medidas.length ? `${medidas.map(formato.numero).join(" × ")} cm` : null;
    }

    function tarjetaNecesidad(n) {
        const [emoji, color] = visualCategoria(n.categoria.codigo);
        return html`<a class="necesidad-tarjeta" href="/app/necesidades/${n.id}">
            <div class="necesidad-tarjeta__cabecera">
                <span class="necesidad-tarjeta__emoji" style="background:${color}" aria-hidden="true">${emoji}</span>
                <div>
                    <span class="necesidad-tarjeta__busca">Busca ${n.categoria.nombre.toLowerCase()}</span>
                    <h3>${n.titulo}</h3>
                </div>
            </div>
            <div class="necesidad-tarjeta__datos">
                <span class="etiqueta">${formato.cantidad(n.cantidad, n.unidad_medida)}</span>
                <span class="etiqueta">${etiqueta("estado_material", n.estado_minimo)} o mejor</span>
                ${n.presupuesto_maximo != null ? html`<span class="etiqueta etiqueta--verde">Hasta ${formato.moneda(n.presupuesto_maximo)}</span>` : ""}
                ${n.estado !== "ABIERTA" ? insigniaEstado(n.estado) : ""}
            </div>
            <div class="necesidad-tarjeta__pie">
                <span><strong>${n.empresa.nombre}</strong> · 📍 ${n.empresa.ubicacion.ciudad}</span>
                <span>${formato.haceCuanto(n.creado_en)}</span>
            </div>
        </a>`;
    }

    let categoriasCache = null;
    const categorias = () => (categoriasCache = categoriasCache || Api.categorias.listar());

    /* ------------------------------------------------------------------ lista */

    R.pagina("necesidades", async () => {
        const formulario = $("#filtros-necesidades");
        const resultados = $("#resultados");
        const chips = $("#chips-categorias");
        const campoCategoria = formulario.elements.categoria_id;
        let pagina = 1;
        let peticion = 0;

        const inicial = R.parametrosUrl();
        R.rellenarFormulario(formulario, inicial);
        pagina = Number(inicial.pagina) || 1;

        const lista = await categorias();
        const pintarChips = () => {
            const actual = String(campoCategoria.value);
            pintar(chips, [
                html`<button type="button" class="chip" data-id="" aria-pressed="${!actual}">Todas</button>`,
                ...lista.map((c) => html`<button type="button" class="chip" data-id="${c.id}" aria-pressed="${actual === String(c.id)}">${visualCategoria(c.codigo)[0]} ${c.nombre}</button>`),
            ]);
        };
        pintarChips();
        chips.addEventListener("click", (e) => {
            const chip = e.target.closest(".chip");
            if (!chip) return;
            campoCategoria.value = chip.dataset.id;
            pintarChips();
            buscar(1);
        });

        async function buscar(nuevaPagina = pagina) {
            pagina = nuevaPagina;
            const filtros = R.formularioAObjeto(formulario);
            const url = new URLSearchParams({ ...filtros, ...(pagina > 1 ? { pagina } : {}) });
            history.replaceState(null, "", `?${url}`);
            const numero = ++peticion;
            try {
                const datos = await Api.necesidades.listar({ ...filtros, pagina, tamano: 12 });
                if (numero !== peticion) return;
                $("#resumen").textContent = datos.total === 1 ? "1 necesidad" : `${formato.numero(datos.total)} necesidades`;
                resultados.style.display = datos.elementos.length ? "" : "block";
                pintar(
                    resultados,
                    datos.elementos.length
                        ? datos.elementos.map(tarjetaNecesidad)
                        : vacio({ icono: "📋", titulo: "No hay necesidades con esos filtros", mensaje: "Prueba con otra categoría o búsqueda." })
                );
                R.paginacion($("#paginacion"), datos, (p) => {
                    buscar(p);
                    window.scrollTo({ top: 0, behavior: "smooth" });
                });
            } catch (error) {
                if (numero === peticion) pintar(resultados, errorCarga(error));
            }
        }

        let espera;
        formulario.addEventListener("input", (e) => {
            if (e.target.type !== "search") return;
            clearTimeout(espera);
            espera = setTimeout(() => buscar(1), 350);
        });
        formulario.addEventListener("change", (e) => e.target.type !== "search" && buscar(1));
        formulario.addEventListener("submit", (e) => {
            e.preventDefault();
            buscar(1);
        });
        buscar();
    });

    /* ---------------------------------------------------------------- detalle */

    R.pagina("necesidad-detalle", async ({ necesidadId }) => {
        const contenedor = $("#necesidad");
        let n;
        try {
            n = await Api.necesidades.obtener(necesidadId);
        } catch (error) {
            pintar(contenedor, error.estado === 404
                ? vacio({ icono: "📋", titulo: "Esta necesidad no existe", accion: html`<a class="boton" href="/app/necesidades">Ver necesidades</a>` })
                : errorCarga(error));
            return;
        }

        const sesion = R.sesion;
        const esPropia = Boolean(sesion && sesion.empresa_id === n.empresa.id);
        const [emoji, color] = visualCategoria(n.categoria.codigo);
        const dimensiones = textoDimensiones(n.dimensiones_minimas);
        const u = n.empresa.ubicacion;
        document.title = `${n.titulo} · REVALORA`;
        $("#migas-titulo").textContent = n.titulo;

        pintar(
            contenedor,
            html`<div class="detalle">
                <div class="pila pila--lg">
                    <div>
                        <div class="necesidad-cabecera">
                            <span class="necesidad-tarjeta__emoji" style="background:${color}" aria-hidden="true">${emoji}</span>
                            <div>
                                <div class="fila"><span class="necesidad-tarjeta__busca">Busca ${n.categoria.nombre.toLowerCase()}</span>${insigniaEstado(n.estado)}</div>
                                <h1>${n.titulo}</h1>
                                <p class="texto-sm texto-tenue" style="margin:0">Publicada ${formato.haceCuanto(n.creado_en)} · actualizada el ${formato.fecha(n.actualizado_en)}</p>
                            </div>
                        </div>
                        <dl class="especificaciones">
                            <div><dt>Cantidad</dt><dd>${formato.cantidad(n.cantidad, n.unidad_medida)}</dd></div>
                            <div><dt>Estado mínimo</dt><dd>${etiqueta("estado_material", n.estado_minimo)}</dd></div>
                            <div><dt>Presupuesto</dt><dd>${n.presupuesto_maximo != null ? `Hasta ${formato.moneda(n.presupuesto_maximo)}` : "No indicado"}</dd></div>
                            ${dimensiones ? html`<div><dt>Medidas mínimas</dt><dd>${dimensiones}</dd></div>` : ""}
                        </dl>
                        ${n.descripcion ? html`<h2>Descripción</h2><p class="detalle__descripcion">${n.descripcion}</p>` : ""}
                    </div>
                    <div id="coincidencias-necesidad"></div>
                </div>

                <aside class="panel-accion">
                    <div class="tarjeta tarjeta__cuerpo pila" id="accion-necesidad"></div>
                    <div class="tarjeta tarjeta__cuerpo">
                        <a class="empresa-mini" href="/app/empresas/${n.empresa.id}">
                            <span class="avatar" aria-hidden="true">${formato.iniciales(n.empresa.nombre)}</span>
                            <div><strong>${n.empresa.nombre}</strong><span>${etiqueta("tipo_empresa", n.empresa.tipo)} · 📍 ${[u.ciudad, u.region].filter(Boolean).join(", ")}</span></div>
                        </a>
                    </div>
                </aside>
            </div>`
        );

        const accion = $("#accion-necesidad");
        if (esPropia) {
            pintar(
                accion,
                html`<div class="alerta alerta--info"><p>Esta es tu necesidad. Abajo verás los sobrantes compatibles.</p></div>
                <div class="campo">
                    <label for="cambiar-estado">Estado</label>
                    <select id="cambiar-estado">
                        ${Object.keys(R.etiquetas.estado_necesidad).map((e) => html`<option value="${e}" ${e === n.estado ? crudo("selected") : ""}>${etiqueta("estado_necesidad", e)}</option>`)}
                    </select>
                    <p class="campo__ayuda">Márcala como atendida cuando consigas el material.</p>
                </div>
                <a class="boton boton--bloque" href="/app/necesidades/${n.id}/editar">${crudo(ICONO_EDITAR)} Editar necesidad</a>`
            );
            $("#cambiar-estado").addEventListener("change", async (e) => {
                try {
                    await Api.necesidades.estado(n.id, e.target.value);
                    avisar(`Necesidad marcada como ${etiqueta("estado_necesidad", e.target.value).toLowerCase()}.`);
                    n.estado = e.target.value;
                } catch (error) {
                    e.target.value = n.estado;
                    avisar(error.message, "error");
                }
            });
            RevaloraCoincidencia.panel($("#coincidencias-necesidad"), { tipo: "necesidad", id: n.id });
        } else {
            pintar(
                accion,
                html`<h3 style="margin:0">¿Tienes este material?</h3>
                <p class="texto-sm texto-secundario" style="margin:0">${n.empresa.nombre} lo está buscando. Publícalo como sobrante: si es compatible, le aparecerá en sus coincidencias y podrá enviarte una solicitud.</p>
                ${sesion && sesion.empresa_id
                    ? html`<a class="boton boton--acento boton--bloque" href="/app/materiales/publicar">Publicar un sobrante</a>
                        <a class="boton boton--secundario boton--bloque" href="/app/mis-materiales">Ver mis materiales</a>`
                    : html`<a class="boton boton--bloque" href="${sesion ? "/app/empresa" : `/app/ingresar?siguiente=${encodeURIComponent(location.pathname)}`}">${sesion ? "Registrar mi empresa" : "Ingresar"}</a>`}`
            );
        }
    });

    /* ------------------------------------------------------ publicar / editar */

    R.pagina("necesidad-formulario", async ({ necesidadId }) => {
        const formulario = $("#formulario-necesidad");
        const select = $("#categoria_id");
        (await categorias()).forEach((c) => select.add(new Option(c.nombre, c.id)));

        const preseleccion = R.parametrosUrl().categoria_id;
        if (preseleccion) select.value = preseleccion;

        if (necesidadId) {
            const n = await Api.necesidades.obtener(necesidadId);
            if (!R.sesion || n.empresa.id !== R.sesion.empresa_id) {
                irA(`/app/necesidades/${necesidadId}`, "Solo puedes editar tus propias necesidades.", "error");
                return;
            }
            R.rellenarFormulario(formulario, { ...n, categoria_id: n.categoria.id });
        }

        R.manejarFormulario(formulario, async (datos) => {
            if (!datos.dimensiones_minimas || !Object.keys(datos.dimensiones_minimas).length) datos.dimensiones_minimas = null;
            if (necesidadId) {
                await Api.necesidades.actualizar(necesidadId, datos);
                irA(`/app/necesidades/${necesidadId}`, "Los cambios se guardaron.");
            } else {
                const n = await Api.necesidades.publicar(datos);
                irA(`/app/necesidades/${n.id}`, "¡Necesidad publicada! Estas son sus coincidencias.");
            }
        });
    });

    /* -------------------------------------------------------- mis necesidades */

    R.pagina("mis-necesidades", () => {
        const contenedor = $("#mis-necesidades");
        const pestanas = $$("#pestanas-estado .pestana");
        let estado = "";

        async function cargar(pagina = 1) {
            let datos;
            try {
                datos = await Api.necesidades.mias({ estado, pagina, tamano: 20 });
            } catch (error) {
                pintar(contenedor, errorCarga(error));
                return;
            }
            if (!datos.elementos.length) {
                pintar(contenedor, vacio({
                    icono: "📋",
                    titulo: estado ? `No tienes necesidades ${etiqueta("estado_necesidad", estado).toLowerCase()}s` : "Todavía no has publicado necesidades",
                    mensaje: "Cuéntanos qué material buscas y te mostraremos los sobrantes compatibles.",
                    accion: html`<a class="boton boton--acento" href="/app/necesidades/publicar">Publicar necesidad</a>`,
                }));
                $("#paginacion").innerHTML = "";
                return;
            }
            pintar(
                contenedor,
                html`<div class="tabla-contenedor"><table class="tabla">
                    <thead><tr><th>Necesidad</th><th>Cantidad</th><th>Presupuesto</th><th>Estado</th><th>Publicada</th><th><span class="solo-lectores">Acciones</span></th></tr></thead>
                    <tbody>${datos.elementos.map((n) => {
                        const [emoji, color] = visualCategoria(n.categoria.codigo);
                        return html`<tr class="${n.estado === "CERRADA" ? "fila-retirada" : ""}">
                            <td><div class="celda-material">
                                <span class="miniatura-tabla" style="--fondo-categoria:${color}">${emoji}</span>
                                <div><a href="/app/necesidades/${n.id}">${n.titulo}</a><span>${n.categoria.nombre}</span></div>
                            </div></td>
                            <td>${formato.cantidad(n.cantidad, n.unidad_medida)}</td>
                            <td>${n.presupuesto_maximo != null ? formato.moneda(n.presupuesto_maximo) : html`<span class="texto-tenue">—</span>`}</td>
                            <td>${insigniaEstado(n.estado)}</td>
                            <td class="texto-tenue">${formato.fecha(n.creado_en)}</td>
                            <td><div class="acciones-tabla">
                                <a class="boton boton--secundario boton--sm" href="/app/necesidades/${n.id}">Ver coincidencias</a>
                                ${n.estado !== "CERRADA" ? html`
                                    <a class="boton boton--fantasma boton--sm" href="/app/necesidades/${n.id}/editar" title="Editar">${crudo(ICONO_EDITAR)}<span class="solo-lectores">Editar</span></a>
                                    <button type="button" class="boton boton--fantasma boton--sm" data-cerrar="${n.id}" title="Cerrar">${crudo(ICONO_X)}<span class="solo-lectores">Cerrar</span></button>` : ""}
                            </div></td>
                        </tr>`;
                    })}</tbody>
                </table></div>`
            );
            R.paginacion($("#paginacion"), datos, cargar);

            $$("[data-cerrar]", contenedor).forEach((boton) =>
                boton.addEventListener("click", async () => {
                    const ok = await R.confirmar({
                        titulo: "¿Cerrar esta necesidad?",
                        mensaje: "Dejará de mostrarse y de recibir coincidencias. El registro se conserva.",
                        aceptar: "Cerrar necesidad",
                        peligro: true,
                    });
                    if (!ok) return;
                    try {
                        await Api.necesidades.cerrar(boton.dataset.cerrar);
                        avisar("La necesidad se cerró.");
                        cargar(datos.pagina);
                    } catch (error) {
                        avisar(error.message, "error");
                    }
                })
            );
        }

        pestanas.forEach((pestana) =>
            pestana.addEventListener("click", () => {
                pestanas.forEach((p) => p.setAttribute("aria-selected", String(p === pestana)));
                estado = pestana.dataset.estado;
                cargar(1);
            })
        );
        cargar();
    });

    window.RevaloraNecesidad = { tarjetaNecesidad };
})();
