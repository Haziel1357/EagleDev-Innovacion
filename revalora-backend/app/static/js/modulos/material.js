/* REVALORA · módulo material: tarjetas, catálogo, detalle, formulario de
 * publicación/edición y "mis materiales". También pinta los materiales
 * recientes y las categorías de la página de inicio. */

(function () {
    "use strict";

    const R = Revalora;
    const { $, $$, html, crudo, pintar, formato, etiqueta, visualCategoria, avisar, irA, vacio, errorCarga } = R;

    const ICONO_VERIFICADO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5z"/><path d="m9 12 2 2 4-4"/></svg>';
    const ICONO_ESTRELLA = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.2L5.8 21 7 14.2 2 9.3l6.9-1z"/></svg>';
    const ICONO_BASURA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg>';
    const ICONO_SUBIR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>';
    const ICONO_EDITAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>';

    /* -------------------------------------------------------------- ayudas */

    const fotoPrincipal = (m) => m.fotos.find((f) => f.es_principal) || m.fotos[0] || null;

    function textoPrecio(m) {
        if (m.tipo_oferta === "APROVECHAMIENTO") return "Gratis";
        if (m.precio !== null && m.precio !== undefined) return formato.moneda(m.precio);
        return m.tipo_oferta === "INTERCAMBIO" ? "Para intercambio" : "A convenir";
    }

    /** El precio de un material es por unidad de medida: "$25.000 / kg". */
    function precioConUnidad(m) {
        const conPrecio = m.tipo_oferta !== "APROVECHAMIENTO" && m.precio !== null && m.precio !== undefined;
        return conPrecio
            ? html`${textoPrecio(m)}<small class="precio-unidad"> / ${etiqueta("unidad_corta", m.unidad_medida)}</small>`
            : textoPrecio(m);
    }

    function textoDimensiones(d) {
        const medidas = [d.largo_cm, d.ancho_cm, d.alto_cm].filter((v) => v !== null && v !== undefined);
        return medidas.length ? `${medidas.map(formato.numero).join(" × ")} cm` : null;
    }

    const insigniaOferta = (m) => html`<span class="etiqueta oferta-${m.tipo_oferta}">${etiqueta("tipo_oferta", m.tipo_oferta)}</span>`;

    const insigniaVerificado = (m) =>
        m.verificado_ia ? html`<span class="etiqueta verificado" title="La IA confirmó el material de la foto">${crudo(ICONO_VERIFICADO)} Verificado</span>` : "";

    const COLOR_DISPONIBILIDAD = { DISPONIBLE: "verde", RESERVADO: "aviso", AGOTADO: "error", RETIRADO: "" };

    const insigniaDisponibilidad = (valor) =>
        html`<span class="etiqueta etiqueta--${COLOR_DISPONIBILIDAD[valor]}"><span class="punto"></span> ${etiqueta("disponibilidad", valor)}</span>`;

    function imagenMaterial(m, claseEmoji = "material-tarjeta__emoji") {
        const foto = fotoPrincipal(m);
        const [emoji] = visualCategoria(m.categoria.codigo);
        return foto ? html`<img src="${foto.url}" alt="${m.titulo}" loading="lazy">` : html`<span class="${claseEmoji}" aria-hidden="true">${emoji}</span>`;
    }

    function tarjetaMaterial(m) {
        const [, color] = visualCategoria(m.categoria.codigo);
        const u = m.empresa.ubicacion;
        return html`<a class="material-tarjeta" href="/materiales/${m.id}">
            <div class="material-tarjeta__imagen" style="--fondo-categoria:${color}">
                ${imagenMaterial(m)}
                <div class="material-tarjeta__insignias">${insigniaOferta(m)}${insigniaVerificado(m)}</div>
            </div>
            <div class="material-tarjeta__cuerpo">
                <span class="material-tarjeta__categoria">${m.categoria.nombre}</span>
                <h3>${m.titulo}</h3>
                <div class="material-tarjeta__datos">${formato.cantidad(m.cantidad, m.unidad_medida)} · Estado ${etiqueta("estado_material", m.estado).toLowerCase()}</div>
                <div class="material-tarjeta__pie">
                    <span class="material-tarjeta__precio">${precioConUnidad(m)}</span>
                    <span class="material-tarjeta__empresa">
                        <strong>${m.empresa.nombre}</strong>
                        📍 ${u.ciudad}${m.distancia_km !== null && m.distancia_km !== undefined ? ` · ${formato.distancia(m.distancia_km)}` : ""}
                    </span>
                </div>
            </div>
        </a>`;
    }

    let categoriasCache = null;
    const categorias = () => (categoriasCache = categoriasCache || Api.categorias.listar());

    /* ---------------------------------------------------------------- inicio */

    R.pagina("inicio", async () => {
        const [lista, recientes] = await Promise.allSettled([categorias(), Api.materiales.listar({ tamano: 8 })]);

        const contenedorCategorias = $("#categorias-inicio");
        if (lista.status === "fulfilled") {
            pintar(
                contenedorCategorias,
                lista.value.map((c) => {
                    const [emoji, color] = visualCategoria(c.codigo);
                    return html`<a class="categoria-inicio" href="/materiales?categoria_id=${c.id}">
                        <span class="categoria-inicio__emoji" style="background:${color}" aria-hidden="true">${emoji}</span>${c.nombre}
                    </a>`;
                })
            );
        } else {
            contenedorCategorias.innerHTML = "";
        }

        const contenedor = $("#recientes");
        if (recientes.status === "rejected") {
            pintar(contenedor, errorCarga(recientes.reason));
        } else if (!recientes.value.elementos.length) {
            contenedor.style.display = "block";
            pintar(
                contenedor,
                vacio({
                    icono: "🌱",
                    titulo: "Aún no hay materiales publicados",
                    mensaje: "Sé la primera empresa en darle una segunda vida a sus sobrantes.",
                    accion: html`<a class="boton" href="/materiales/publicar">Publicar un sobrante</a>`,
                })
            );
        } else {
            pintar(contenedor, recientes.value.elementos.map(tarjetaMaterial));
        }
    });

    /* -------------------------------------------------------------- catálogo */

    R.pagina("materiales", async () => {
        const formulario = $("#filtros-materiales");
        const resultados = $("#resultados");
        const resumen = $("#resumen");
        const chips = $("#chips-categorias");
        const campoCategoria = formulario.elements.categoria_id;
        const TAMANO = 12;
        let pagina = 1;
        let peticion = 0;

        if (window.matchMedia("(max-width: 960px)").matches) $("#filtros-plegables").open = false;

        // Estado inicial desde la URL (permite compartir búsquedas).
        const inicial = R.parametrosUrl();
        R.rellenarFormulario(formulario, { ...inicial, solo_verificados: inicial.solo_verificados === "true" });
        pagina = Number(inicial.pagina) || 1;

        const lista = await categorias();
        const pintarChips = () => {
            const actual = campoCategoria.value;
            pintar(
                chips,
                [
                    html`<button type="button" class="chip" data-id="" aria-pressed="${!actual}">Todas</button>`,
                    ...lista.map((c) => {
                        const [emoji] = visualCategoria(c.codigo);
                        return html`<button type="button" class="chip" data-id="${c.id}" aria-pressed="${String(actual) === String(c.id)}">${emoji} ${c.nombre}</button>`;
                    }),
                ]
            );
        };
        pintarChips();
        chips.addEventListener("click", (evento) => {
            const chip = evento.target.closest(".chip");
            if (!chip) return;
            campoCategoria.value = chip.dataset.id;
            pintarChips();
            buscar(1);
        });

        async function buscar(nuevaPagina = pagina) {
            pagina = nuevaPagina;
            const filtros = R.formularioAObjeto(formulario);
            if (!filtros.solo_verificados) delete filtros.solo_verificados;

            const url = new URLSearchParams({ ...filtros, ...(pagina > 1 ? { pagina } : {}) });
            history.replaceState(null, "", url.toString() ? `?${url}` : location.pathname);

            const numero = ++peticion;
            resultados.setAttribute("aria-busy", "true");
            try {
                const datos = await Api.buscador.tradicional({ ...filtros, pagina, tamano: TAMANO });
                if (numero !== peticion) return; // llegó una búsqueda más reciente
                resumen.textContent = datos.total === 1 ? "1 material encontrado" : `${formato.numero(datos.total)} materiales encontrados`;
                if (!datos.elementos.length) {
                    resultados.style.display = "block";
                    pintar(
                        resultados,
                        vacio({
                            icono: "🔍",
                            titulo: "No encontramos materiales con esos filtros",
                            mensaje: "Prueba con otra búsqueda o quita algunos filtros.",
                            accion: html`<button type="button" class="boton boton--secundario" data-limpiar>Limpiar filtros</button>`,
                        })
                    );
                    $("[data-limpiar]", resultados).addEventListener("click", limpiar);
                } else {
                    resultados.style.display = "";
                    pintar(resultados, datos.elementos.map(tarjetaMaterial));
                }
                R.paginacion($("#paginacion"), datos, (p) => {
                    buscar(p);
                    window.scrollTo({ top: 0, behavior: "smooth" });
                });
            } catch (error) {
                if (numero !== peticion) return;
                resumen.textContent = "";
                resultados.style.display = "block";
                pintar(resultados, vacio({ icono: "⚠️", titulo: "No se pudo realizar la búsqueda", mensaje: error.message }));
                $("#paginacion").innerHTML = "";
            } finally {
                if (numero === peticion) resultados.removeAttribute("aria-busy");
            }
        }

        function limpiar() {
            formulario.reset();
            $$('input[type="hidden"]', formulario).forEach((campo) => (campo.value = ""));
            pintarChips();
            buscar(1);
        }

        let espera;
        formulario.addEventListener("input", (evento) => {
            if (evento.target.type !== "search" && evento.target.type !== "number" && evento.target.name !== "ciudad") return;
            clearTimeout(espera);
            espera = setTimeout(() => buscar(1), 350);
        });
        // Ordenar por cercanía o filtrar por distancia necesita un punto de partida: la
        // ubicación de la empresa (la pone el backend) o la del navegador.
        const tieneOrigen = () =>
            Boolean(formulario.elements.latitud.value) || Boolean(R.sesion && R.sesion.empresa_id);

        formulario.addEventListener("change", async (evento) => {
            const nombre = evento.target.name;
            if (["texto", "precio_maximo", "ciudad"].includes(nombre)) return;
            const necesitaOrigen = (nombre === "orden" && evento.target.value === "cercania") || (nombre === "radio_km" && evento.target.value);
            if (necesitaOrigen && !tieneOrigen()) {
                try {
                    await usarUbicacion();
                } catch (error) {
                    avisar(error.message, "aviso");
                    evento.target.value = nombre === "orden" ? "recientes" : "";
                }
            }
            buscar(1);
        });
        formulario.addEventListener("submit", (evento) => {
            evento.preventDefault();
            buscar(1);
        });
        $("#limpiar-filtros").addEventListener("click", limpiar);

        const botonUbicacion = $("#usar-ubicacion");
        async function usarUbicacion() {
            await R.conCarga(botonUbicacion, async () => {
                const { latitud, longitud } = await R.obtenerUbicacion();
                formulario.elements.latitud.value = latitud;
                formulario.elements.longitud.value = longitud;
                $("#ayuda-distancia").textContent = "Se mide desde tu ubicación actual.";
            });
        }
        botonUbicacion.addEventListener("click", async () => {
            try {
                await usarUbicacion();
                buscar(1);
            } catch (error) {
                avisar(error.message, "aviso");
            }
        });

        buscar();
    });

    /* --------------------------------------------------------------- detalle */

    R.pagina("material-detalle", async ({ materialId }) => {
        const contenedor = $("#material");
        let material;
        try {
            material = await Api.materiales.obtener(materialId);
        } catch (error) {
            pintar(
                contenedor,
                error.estado === 404
                    ? vacio({
                          icono: "📦",
                          titulo: "Este material no existe o fue retirado",
                          accion: html`<a class="boton" href="/materiales">Ver otros materiales</a>`,
                      })
                    : errorCarga(error)
            );
            return;
        }

        const sesion = R.sesion;
        const esPropio = Boolean(sesion && sesion.empresa_id === material.empresa.id);
        let fotoActual = fotoPrincipal(material);

        document.title = `${material.titulo} · REVALORA`;
        $("#migas-titulo").textContent = material.titulo;

        function pintarGaleria() {
            const [, color] = visualCategoria(material.categoria.codigo);
            const [emoji] = visualCategoria(material.categoria.codigo);
            const galeria = $("#galeria");
            pintar(
                galeria,
                html`<div class="galeria__principal" style="--fondo-categoria:${color}">
                    ${fotoActual ? html`<img src="${fotoActual.url}" alt="${material.titulo}">` : html`<span class="material-tarjeta__emoji" aria-hidden="true">${emoji}</span>`}
                </div>
                ${material.fotos.length > 1 || esPropio ? html`<div class="galeria__miniaturas">
                    ${material.fotos.map((f) => html`<div class="miniatura" role="button" tabindex="0" data-foto="${f.id}" aria-current="${fotoActual && f.id === fotoActual.id}" aria-label="Ver foto">
                        <img src="${f.url}" alt="">
                        ${esPropio ? html`<div class="miniatura__acciones">
                            <button type="button" class="miniatura__accion miniatura__accion--principal" data-principal="${f.id}" aria-pressed="${f.es_principal}" title="Usar como foto principal">${crudo(ICONO_ESTRELLA)}</button>
                            <button type="button" class="miniatura__accion" data-eliminar-foto="${f.id}" title="Eliminar foto">${crudo(ICONO_BASURA)}</button>
                        </div>` : ""}
                    </div>`)}
                    ${esPropio ? html`<label class="miniatura miniatura--subir" title="Agregar fotos">
                        ${crudo(ICONO_SUBIR)}<span class="solo-lectores">Agregar fotos</span>
                        <input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden data-subir-fotos>
                    </label>` : ""}
                </div>` : ""}`
            );

            $$("[data-foto]", galeria).forEach((miniatura) => {
                const ver = () => {
                    fotoActual = material.fotos.find((f) => String(f.id) === miniatura.dataset.foto);
                    pintarGaleria();
                };
                miniatura.addEventListener("click", (e) => !e.target.closest("button") && ver());
                miniatura.addEventListener("keydown", (e) => e.key === "Enter" && ver());
            });

            if (!esPropio) return;
            $$("[data-principal]", galeria).forEach((boton) =>
                boton.addEventListener("click", async () => {
                    try {
                        await Api.materiales.fotoPrincipal(material.id, boton.dataset.principal);
                        await recargar();
                        avisar("Foto principal actualizada.", "exito", 2500);
                    } catch (error) {
                        avisar(error.message, "error");
                    }
                })
            );
            $$("[data-eliminar-foto]", galeria).forEach((boton) =>
                boton.addEventListener("click", async () => {
                    const ok = await R.confirmar({ titulo: "¿Eliminar esta foto?", mensaje: "La foto dejará de mostrarse en la publicación.", aceptar: "Eliminar", peligro: true });
                    if (!ok) return;
                    try {
                        await Api.materiales.eliminarFoto(material.id, boton.dataset.eliminarFoto);
                        await recargar();
                        avisar("Foto eliminada.", "exito", 2500);
                    } catch (error) {
                        avisar(error.message, "error");
                    }
                })
            );
            const subir = $("[data-subir-fotos]", galeria);
            subir.addEventListener("change", async () => {
                const archivos = [...subir.files];
                const problema = archivos.map(RevaloraIA.validarArchivo).find(Boolean);
                if (problema) {
                    avisar(problema, "error");
                    return;
                }
                try {
                    await Api.materiales.subirFotos(material.id, archivos);
                    await recargar();
                    avisar(archivos.length === 1 ? "Foto agregada." : "Fotos agregadas.");
                } catch (error) {
                    avisar(error.message, "error");
                }
            });
        }

        async function recargar() {
            material = await Api.materiales.obtener(material.id);
            fotoActual = material.fotos.find((f) => fotoActual && f.id === fotoActual.id) || fotoPrincipal(material);
            pintarGaleria();
        }

        const u = material.empresa.ubicacion;
        const dimensiones = textoDimensiones(material.dimensiones);
        const disponible = material.disponibilidad === "DISPONIBLE";

        pintar(
            contenedor,
            html`<div class="detalle">
                <div class="pila pila--lg">
                    <div class="galeria" id="galeria"></div>
                    <div class="detalle__info">
                        <div class="fila">
                            <span class="material-tarjeta__categoria">${material.categoria.nombre}</span>
                            ${insigniaVerificado(material)}
                            ${material.disponibilidad !== "DISPONIBLE" ? insigniaDisponibilidad(material.disponibilidad) : ""}
                        </div>
                        <h1>${material.titulo}</h1>
                        <p class="texto-sm texto-tenue">Publicado ${formato.haceCuanto(material.creado_en)} · actualizado el ${formato.fecha(material.actualizado_en)}</p>

                        <dl class="especificaciones">
                            <div><dt>Cantidad</dt><dd>${formato.cantidad(material.cantidad, material.unidad_medida)}</dd></div>
                            <div><dt>Estado</dt><dd>${etiqueta("estado_material", material.estado)}</dd></div>
                            <div><dt>Oferta</dt><dd>${etiqueta("tipo_oferta", material.tipo_oferta)}</dd></div>
                            ${dimensiones ? html`<div><dt>Dimensiones</dt><dd>${dimensiones}</dd></div>` : ""}
                            ${material.distancia_km != null ? html`<div><dt>Distancia</dt><dd>${formato.distancia(material.distancia_km)}</dd></div>` : ""}
                        </dl>

                        ${material.descripcion ? html`<h2>Descripción</h2><p class="detalle__descripcion">${material.descripcion}</p>` : ""}
                    </div>
                    ${esPropio ? html`<div id="coincidencias-material"></div>` : ""}
                </div>

                <aside class="panel-accion">
                    <div class="tarjeta tarjeta__cuerpo pila">
                        <div class="fila fila--entre">${insigniaOferta(material)}${insigniaDisponibilidad(material.disponibilidad)}</div>
                        <div class="panel-accion__precio">${precioConUnidad(material)}
                            <small>${material.tipo_oferta === "VENTA"
                                ? `${formato.cantidad(material.cantidad, material.unidad_medida)} disponibles`
                                : material.tipo_oferta === "INTERCAMBIO"
                                  ? `Se intercambia por otro material${material.precio != null ? " (valor de referencia)" : ""}`
                                  : "Para aprovechamiento sin costo"}</small>
                        </div>
                        <div id="accion-material"></div>
                    </div>

                    <div class="tarjeta tarjeta__cuerpo">
                        <a class="empresa-mini" href="/empresas/${material.empresa.id}">
                            <span class="avatar" aria-hidden="true">${formato.iniciales(material.empresa.nombre)}</span>
                            <div>
                                <strong>${material.empresa.nombre}</strong>
                                <span>${etiqueta("tipo_empresa", material.empresa.tipo)} · 📍 ${[u.ciudad, u.region].filter(Boolean).join(", ")}</span>
                            </div>
                        </a>
                    </div>
                </aside>
            </div>`
        );
        pintarGaleria();

        const accion = $("#accion-material");
        if (esPropio) {
            pintarAccionesPropias(accion, material);
            RevaloraCoincidencia.panel($("#coincidencias-material"), { tipo: "material", id: material.id });
        } else if (!sesion) {
            pintar(accion, html`<p class="texto-sm texto-secundario">Ingresa para solicitar este material.</p>
                <a class="boton boton--lg boton--bloque" href="/ingresar?siguiente=${encodeURIComponent(location.pathname)}">Ingresar para solicitarlo</a>`);
        } else if (!sesion.empresa_id) {
            pintar(accion, html`<p class="texto-sm texto-secundario">Las solicitudes se hacen a nombre de una empresa.</p>
                <a class="boton boton--lg boton--bloque" href="/empresa?siguiente=${encodeURIComponent(location.pathname)}">Registrar mi empresa</a>`);
        } else if (!disponible) {
            pintar(accion, html`<div class="alerta alerta--info"><p>Este material no está disponible en este momento.</p></div>`);
        } else {
            await RevaloraTransaccion.formularioSolicitud(accion, material);
        }
    });

    function pintarAccionesPropias(contenedor, material) {
        const opciones = ["DISPONIBLE", "RESERVADO", "AGOTADO"];
        pintar(
            contenedor,
            html`<div class="pila">
                <div class="alerta alerta--info"><p>Esta es tu publicación.</p></div>
                <div class="campo">
                    <label for="cambiar-disponibilidad">Disponibilidad</label>
                    <select id="cambiar-disponibilidad">
                        ${opciones.map((o) => html`<option value="${o}" ${o === material.disponibilidad ? crudo("selected") : ""}>${etiqueta("disponibilidad", o)}</option>`)}
                    </select>
                </div>
                <a class="boton boton--bloque" href="/materiales/${material.id}/editar">${crudo(ICONO_EDITAR)} Editar publicación</a>
                <button type="button" class="boton boton--peligro boton--bloque" data-retirar>${crudo(ICONO_BASURA)} Retirar publicación</button>
            </div>`
        );
        $("#cambiar-disponibilidad", contenedor).addEventListener("change", async (evento) => {
            try {
                await Api.materiales.disponibilidad(material.id, evento.target.value);
                avisar(`Ahora el material está ${etiqueta("disponibilidad", evento.target.value).toLowerCase()}.`);
            } catch (error) {
                avisar(error.message, "error");
                evento.target.value = material.disponibilidad;
            }
        });
        $("[data-retirar]", contenedor).addEventListener("click", () => retirar(material, () => irA("/mis-materiales", "La publicación fue retirada.")));
    }

    async function retirar(material, alTerminar) {
        const ok = await R.confirmar({
            titulo: "¿Retirar esta publicación?",
            mensaje: `“${material.titulo}” dejará de mostrarse a las demás empresas. Su historial se conserva.`,
            aceptar: "Retirar",
            peligro: true,
        });
        if (!ok) return;
        try {
            await Api.materiales.retirar(material.id);
            alTerminar();
        } catch (error) {
            avisar(error.message, "error");
        }
    }

    /* -------------------------------------------------- publicar / editar */

    R.pagina("material-formulario", async ({ materialId }) => {
        const formulario = $("#formulario-material");
        const selectCategoria = $("#categoria_id");
        const campoClasificacion = $("#clasificacion_id");
        const ayudaCategoria = $("#ayuda-categoria");
        let clasificacion = null;
        let fotoSinVerificar = null; // foto que la IA no pudo procesar: se sube como foto normal

        const listaCategorias = await categorias();
        listaCategorias.forEach((c) => selectCategoria.add(new Option(c.nombre, c.id)));

        // Precio según el tipo de oferta.
        function actualizarPrecio() {
            const tipo = formulario.elements.tipo_oferta.value;
            const campoPrecio = $("#campo-precio");
            const precio = $("#precio");
            campoPrecio.hidden = tipo === "APROVECHAMIENTO";
            precio.disabled = tipo === "APROVECHAMIENTO";
            precio.required = tipo === "VENTA";
            $("#etiqueta-precio").innerHTML = tipo === "VENTA" ? "Precio" : 'Valor de referencia <span class="campo__opcional">(opcional)</span>';
            const unidad = etiqueta("unidad_corta", formulario.elements.unidad_medida.value);
            $("#ayuda-precio").textContent =
                tipo === "VENTA" ? `Precio por unidad de medida (por ${unidad}).` : `Ayuda a valorar el intercambio (por ${unidad}).`;
            $("#sufijo-precio").textContent = `COP / ${unidad}`;
        }
        $$('[name="tipo_oferta"]', formulario).forEach((r) => r.addEventListener("change", actualizarPrecio));
        formulario.elements.unidad_medida.addEventListener("change", actualizarPrecio);

        // Aviso cuando la categoría elegida difiere de la que propuso la IA.
        function actualizarAyudaCategoria() {
            if (!clasificacion || !clasificacion.categoria_predicha) {
                ayudaCategoria.textContent = "";
                return;
            }
            const coincide = String(selectCategoria.value) === String(clasificacion.categoria_predicha.id);
            ayudaCategoria.textContent = coincide
                ? "✔ Coincide con la IA: la publicación quedará verificada."
                : "Elegiste una categoría distinta a la de la IA: se guardará como corrección y la publicación no quedará verificada.";
        }
        selectCategoria.addEventListener("change", actualizarAyudaCategoria);

        if (materialId) {
            const material = await Api.materiales.obtener(materialId);
            if (!R.sesion || material.empresa.id !== R.sesion.empresa_id) {
                irA(`/materiales/${materialId}`, "Solo puedes editar tus propias publicaciones.", "error");
                return;
            }
            R.rellenarFormulario(formulario, { ...material, categoria_id: material.categoria.id });
        } else {
            RevaloraIA.reconocimiento($("#reconocimiento-ia"), {
                nombreCategoria: (id) => (listaCategorias.find((c) => c.id === id) || {}).nombre,
                alReconocer(resultado) {
                    clasificacion = resultado;
                    fotoSinVerificar = null;
                    campoClasificacion.value = resultado.id;
                    if (resultado.categoria_predicha) selectCategoria.value = resultado.categoria_predicha.id;
                    if (!formulario.elements.titulo.value && resultado.categoria_predicha) {
                        formulario.elements.titulo.placeholder = `Ej.: Retazos de ${resultado.categoria_predicha.nombre.toLowerCase()}`;
                    }
                    actualizarAyudaCategoria();
                },
                alElegirCategoria(id) {
                    selectCategoria.value = id;
                    actualizarAyudaCategoria();
                },
                alFallar(archivo) {
                    clasificacion = null;
                    campoClasificacion.value = "";
                    fotoSinVerificar = archivo;
                    actualizarAyudaCategoria();
                },
                alQuitar() {
                    clasificacion = null;
                    fotoSinVerificar = null;
                    campoClasificacion.value = "";
                    actualizarAyudaCategoria();
                },
            });

            const entradaFotos = $("#fotos-adicionales");
            entradaFotos.addEventListener("change", () => {
                const archivos = [...entradaFotos.files];
                const problema = archivos.map(RevaloraIA.validarArchivo).find(Boolean);
                if (problema) {
                    avisar(problema, "error");
                    entradaFotos.value = "";
                }
                pintar($("#vistas-previas"), [...entradaFotos.files].map((f) => html`<img src="${URL.createObjectURL(f)}" alt="">`));
            });
        }
        actualizarPrecio();

        R.manejarFormulario(formulario, async (datos) => {
            if (!datos.dimensiones || !Object.keys(datos.dimensiones).length) datos.dimensiones = null;

            if (materialId) {
                await Api.materiales.actualizar(materialId, datos);
                irA(`/materiales/${materialId}`, "Los cambios se guardaron.");
                return;
            }

            const material = await Api.materiales.publicar(datos);
            const fotos = [...(fotoSinVerificar ? [fotoSinVerificar] : []), ...$("#fotos-adicionales").files];
            if (fotos.length) {
                try {
                    await Api.materiales.subirFotos(material.id, fotos);
                } catch (error) {
                    irA(`/materiales/${material.id}`, `El material se publicó, pero no se pudieron subir las fotos: ${error.message}`, "aviso");
                    return;
                }
            }
            irA(
                `/materiales/${material.id}`,
                material.verificado_ia ? "¡Material publicado y verificado con IA!" : "¡Material publicado!"
            );
        });
    });

    /* -------------------------------------------------------- mis materiales */

    R.pagina("mis-materiales", async () => {
        const contenedor = $("#mis-materiales");
        let pagina = 1;

        async function cargar(nuevaPagina = pagina) {
            pagina = nuevaPagina;
            let datos;
            try {
                datos = await Api.materiales.mios({ pagina, tamano: 20 });
            } catch (error) {
                pintar(contenedor, errorCarga(error));
                return;
            }
            if (!datos.elementos.length) {
                pintar(
                    contenedor,
                    vacio({
                        icono: "📦",
                        titulo: "Todavía no has publicado materiales",
                        mensaje: "Toma una foto de lo que te sobra y publícalo en menos de un minuto.",
                        accion: html`<a class="boton boton--acento" href="/materiales/publicar">Publicar mi primer sobrante</a>`,
                    })
                );
                $("#paginacion").innerHTML = "";
                return;
            }

            pintar(
                contenedor,
                html`<div class="tabla-contenedor"><table class="tabla">
                    <thead><tr><th>Material</th><th>Cantidad</th><th>Oferta</th><th>Disponibilidad</th><th>Publicado</th><th><span class="solo-lectores">Acciones</span></th></tr></thead>
                    <tbody>${datos.elementos.map(filaMaterial)}</tbody>
                </table></div>`
            );
            R.paginacion($("#paginacion"), datos, cargar);

            $$("[data-disponibilidad]", contenedor).forEach((select) =>
                select.addEventListener("change", async () => {
                    const anterior = select.dataset.actual;
                    try {
                        await Api.materiales.disponibilidad(select.dataset.disponibilidad, select.value);
                        select.dataset.actual = select.value;
                        avisar("Disponibilidad actualizada.", "exito", 2500);
                    } catch (error) {
                        select.value = anterior;
                        avisar(error.message, "error");
                    }
                })
            );
            $$("[data-retirar]", contenedor).forEach((boton) =>
                boton.addEventListener("click", () => {
                    const material = datos.elementos.find((m) => String(m.id) === boton.dataset.retirar);
                    retirar(material, () => {
                        avisar("La publicación fue retirada.");
                        cargar();
                    });
                })
            );
        }

        function filaMaterial(m) {
            const [, color] = visualCategoria(m.categoria.codigo);
            const retirado = m.disponibilidad === "RETIRADO";
            return html`<tr class="${retirado ? "fila-retirada" : ""}">
                <td><div class="celda-material">
                    <span class="miniatura-tabla" style="--fondo-categoria:${color}">${imagenMaterial(m, "")}</span>
                    <div><a href="/materiales/${m.id}">${m.titulo}</a><span>${m.categoria.nombre} ${m.verificado_ia ? "· ✔ verificado" : ""}</span></div>
                </div></td>
                <td>${formato.cantidad(m.cantidad, m.unidad_medida)}</td>
                <td>${etiqueta("tipo_oferta", m.tipo_oferta)}<br><span class="texto-xs texto-tenue">${precioConUnidad(m)}</span></td>
                <td>${retirado
                    ? insigniaDisponibilidad(m.disponibilidad)
                    : html`<div class="campo"><select class="selector-disponibilidad" data-disponibilidad="${m.id}" data-actual="${m.disponibilidad}" aria-label="Disponibilidad de ${m.titulo}">
                        ${["DISPONIBLE", "RESERVADO", "AGOTADO"].map((o) => html`<option value="${o}" ${o === m.disponibilidad ? crudo("selected") : ""}>${etiqueta("disponibilidad", o)}</option>`)}
                    </select></div>`}</td>
                <td class="texto-tenue">${formato.fecha(m.creado_en)}</td>
                <td><div class="acciones-tabla">${retirado ? "" : html`
                    <a class="boton boton--fantasma boton--sm" href="/materiales/${m.id}/editar" title="Editar">${crudo(ICONO_EDITAR)}<span class="solo-lectores">Editar</span></a>
                    <button type="button" class="boton boton--fantasma boton--sm" data-retirar="${m.id}" title="Retirar">${crudo(ICONO_BASURA)}<span class="solo-lectores">Retirar</span></button>`}
                </div></td>
            </tr>`;
        }

        cargar();
    });

    window.RevaloraMaterial = { tarjetaMaterial, textoPrecio };
})();
