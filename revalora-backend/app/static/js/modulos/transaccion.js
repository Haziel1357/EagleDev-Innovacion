/* REVALORA · módulo transaccion: solicitudes de compra, intercambio o
 * aprovechamiento.
 *
 * - RevaloraTransaccion.formularioSolicitud(contenedor, material): formulario
 *   del detalle de un material; lo envía a POST /solicitudes.
 * - Páginas: lista de solicitudes (recibidas/enviadas), detalle con acciones
 *   según el papel de mi empresa, e historial de operaciones.
 */

(function () {
    "use strict";

    const { html, pintar, $, etiqueta, formato, manejarFormulario, solicitudPorOferta } = Revalora;

    const TEXTOS = {
        COMPRA: { titulo: "Comprar este material", boton: "Enviar solicitud de compra" },
        INTERCAMBIO: { titulo: "Proponer un intercambio", boton: "Proponer intercambio" },
        APROVECHAMIENTO: { titulo: "Solicitar este material", boton: "Solicitar material" },
    };

    async function formularioSolicitud(contenedor, material) {
        const tipo = solicitudPorOferta[material.tipo_oferta];
        const textos = TEXTOS[tipo];
        const unidad = etiqueta("unidad_corta", material.unidad_medida);

        let misMateriales = [];
        if (tipo === "INTERCAMBIO") {
            const pagina = await Api.materiales.mios({ tamano: 100 });
            misMateriales = pagina.elementos.filter((m) => m.disponibilidad === "DISPONIBLE");
        }

        pintar(
            contenedor,
            html`<form class="formulario" novalidate>
                <h3 style="margin:0">${textos.titulo}</h3>
                <div class="alerta alerta--error formulario__error" hidden></div>
                <input type="hidden" name="material_id" value="${material.id}">
                <input type="hidden" name="tipo" value="${tipo}">

                <div class="campo">
                    <label for="solicitud-cantidad">Cantidad que necesitas</label>
                    <div class="campo__con-sufijo">
                        <input id="solicitud-cantidad" name="cantidad" type="number" min="0.001" step="any"
                               max="${Number(material.cantidad)}" value="${Number(material.cantidad)}" required>
                        <span class="campo__sufijo">${unidad}</span>
                    </div>
                    <p class="campo__ayuda">Disponible: ${formato.cantidad(material.cantidad, material.unidad_medida)}</p>
                </div>

                ${tipo === "COMPRA" ? html`<div class="campo">
                    <label for="solicitud-precio">Precio que ofreces por ${unidad} <span class="campo__opcional">(opcional)</span></label>
                    <div class="campo__con-sufijo campo__con-sufijo--ancho">
                        <input id="solicitud-precio" name="precio_ofrecido" type="number" min="0" step="any" placeholder="${Number(material.precio)}">
                        <span class="campo__sufijo">COP / ${unidad}</span>
                    </div>
                    <p class="campo__ayuda">Déjalo vacío para aceptar el precio publicado.</p>
                </div>` : ""}

                ${tipo === "INTERCAMBIO" ? (misMateriales.length
                    ? html`<div class="campo">
                        <label for="solicitud-ofrecido">Material que ofreces a cambio</label>
                        <select id="solicitud-ofrecido" name="material_ofrecido_id" required>
                            <option value="">Elige uno de tus materiales</option>
                            ${misMateriales.map((m) => html`<option value="${m.id}">${m.titulo} · ${formato.cantidad(m.cantidad, m.unidad_medida)}</option>`)}
                        </select>
                    </div>`
                    : html`<div class="alerta alerta--info"><p>Para proponer un intercambio necesitas tener al menos un material disponible.
                        <a href="/materiales/publicar">Publica uno</a>.</p></div>`) : ""}

                <div class="campo">
                    <label for="solicitud-mensaje">Mensaje para ${material.empresa.nombre} <span class="campo__opcional">(opcional)</span></label>
                    <textarea id="solicitud-mensaje" name="mensaje" maxlength="1000" rows="3"
                              placeholder="Cuéntales para qué lo necesitas y cómo prefieres recogerlo."></textarea>
                </div>

                <button class="boton boton--lg boton--bloque" type="submit"
                        ${tipo === "INTERCAMBIO" && !misMateriales.length ? "disabled" : ""}>${textos.boton}</button>
            </form>`
        );

        manejarFormulario($("form", contenedor), async (datos) => {
            const solicitud = await Api.solicitudes.crear(datos);
            pintar(
                contenedor,
                html`<div class="solicitud-enviada">
                    <span class="solicitud-enviada__icono"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span>
                    <h3 style="margin:0">¡Solicitud enviada!</h3>
                    <p class="texto-sm texto-secundario" style="margin:0">
                        ${material.empresa.nombre} revisará tu pedido de
                        ${formato.cantidad(solicitud.cantidad, solicitud.material.unidad_medida)} y podrá aceptarlo o rechazarlo.
                    </p>
                    <span class="etiqueta etiqueta--aviso"><span class="punto"></span> ${etiqueta("estado_solicitud", solicitud.estado)}</span>
                    <a class="boton boton--secundario boton--sm" href="/solicitudes/${solicitud.id}">Ver la solicitud</a>
                </div>`
            );
        });
    }

    /* ------------------------------------------------------------- comunes */

    const R = Revalora;
    const { $$, avisar, vacio, errorCarga, visualCategoria } = R;

    const insigniaEstado = (estado) =>
        html`<span class="etiqueta estado-${estado}"><span class="punto"></span> ${etiqueta("estado_solicitud", estado)}</span>`;

    function miniatura(m, clase) {
        const foto = m.fotos.find((f) => f.es_principal) || m.fotos[0];
        const [emoji, color] = visualCategoria(m.categoria.codigo);
        return html`<span class="${clase}" style="--fondo-categoria:${color}">${foto ? html`<img src="${foto.url}" alt="">` : emoji}</span>`;
    }

    /** Papel de mi empresa en la solicitud. */
    function papel(s) {
        const miEmpresa = R.sesion && R.sesion.empresa_id;
        return {
            soyOfertante: s.material.empresa.id === miEmpresa,
            soySolicitante: s.empresa_solicitante.id === miEmpresa,
        };
    }

    /** Acciones posibles según el estado y el papel (mismas reglas que SolicitudService). */
    function accionesDisponibles(s) {
        const { soyOfertante, soySolicitante } = papel(s);
        const acciones = [];
        if (s.estado === "PENDIENTE" && soyOfertante) acciones.push("aceptar", "rechazar");
        if (s.estado === "PENDIENTE" && soySolicitante) acciones.push("cancelar");
        if (s.estado === "ACEPTADA") acciones.push("completar");
        return acciones;
    }

    const ACCIONES = {
        aceptar: { texto: "Aceptar", clase: "", hecho: "Aceptaste la solicitud." },
        rechazar: { texto: "Rechazar", clase: "boton--peligro", hecho: "Rechazaste la solicitud." },
        cancelar: { texto: "Cancelar solicitud", clase: "boton--peligro", hecho: "Cancelaste la solicitud." },
        completar: { texto: "Marcar como completada", clase: "", hecho: "La operación quedó completada." },
    };

    /** Pide confirmación (con comentario opcional) y ejecuta la acción. */
    function confirmarAccion(s, accion) {
        const cantidad = formato.cantidad(s.cantidad, s.material.unidad_medida);
        const mensajes = {
            aceptar: `Se descontarán ${cantidad} de “${s.material.titulo}”.${s.material_ofrecido ? ` El material ofrecido (“${s.material_ofrecido.titulo}”) quedará reservado.` : ""}`,
            rechazar: `${s.empresa_solicitante.nombre} verá que rechazaste su solicitud.`,
            cancelar: "La empresa dueña del material ya no podrá responderla.",
            completar: "Confirma que la entrega ya se realizó.",
        };
        return new Promise((resolver) => {
            const dialogo = document.createElement("dialog");
            dialogo.className = "dialogo";
            pintar(
                dialogo,
                html`<form method="dialog">
                    <div class="dialogo__cuerpo pila">
                        <div><h2>${ACCIONES[accion].texto}</h2><p class="texto-secundario" style="margin:0">${mensajes[accion]}</p></div>
                        <div class="campo">
                            <label for="comentario-accion">Comentario <span class="campo__opcional">(opcional)</span></label>
                            <textarea id="comentario-accion" maxlength="500" rows="3" placeholder="Ej.: Puedes recogerlo el lunes en la mañana."></textarea>
                        </div>
                    </div>
                    <div class="dialogo__acciones">
                        <button class="boton boton--secundario" value="no">Volver</button>
                        <button class="boton ${ACCIONES[accion].clase}" value="si">${ACCIONES[accion].texto}</button>
                    </div>
                </form>`
            );
            dialogo.addEventListener("close", async () => {
                const comentario = $("#comentario-accion", dialogo).value.trim();
                dialogo.remove();
                if (dialogo.returnValue !== "si") return resolver(null);
                try {
                    const actualizada = await Api.solicitudes.responder(s.id, accion, comentario);
                    avisar(ACCIONES[accion].hecho);
                    resolver(actualizada);
                } catch (error) {
                    avisar(error.message, "error");
                    resolver(null);
                }
            });
            document.body.append(dialogo);
            dialogo.showModal();
        });
    }

    /* ---------------------------------------------------- lista de solicitudes */

    R.pagina("solicitudes", () => {
        const contenedor = $("#solicitudes");
        const pestanas = $$("#pestanas-solicitudes .pestana");
        const filtroEstado = $("#filtro-estado");
        const inicial = R.parametrosUrl();
        let vista = inicial.vista === "enviadas" ? "enviadas" : "recibidas";
        filtroEstado.value = inicial.estado || "";

        function tarjeta(s) {
            const recibida = vista === "recibidas";
            const otra = recibida ? s.empresa_solicitante : s.material.empresa;
            const acciones = accionesDisponibles(s);
            return html`<article class="solicitud ${s.estado === "PENDIENTE" ? "solicitud--pendiente" : ""}">
                ${miniatura(s.material, "solicitud__imagen")}
                <div class="solicitud__info">
                    <div class="solicitud__titulo">
                        <a href="/solicitudes/${s.id}">${etiqueta("tipo_solicitud", s.tipo)} · ${s.material.titulo}</a>
                        ${insigniaEstado(s.estado)}
                    </div>
                    <span class="solicitud__meta">
                        ${recibida ? "De" : "Para"} <strong>${otra.nombre}</strong> · ${formato.cantidad(s.cantidad, s.material.unidad_medida)}
                        ${s.material_ofrecido ? html` · a cambio de <em>${s.material_ofrecido.titulo}</em>` : ""}
                        ${s.precio_ofrecido != null ? html` · ofrece ${formato.moneda(s.precio_ofrecido)}` : ""}
                    </span>
                    <span class="solicitud__fecha">Enviada ${formato.haceCuanto(s.creado_en)}${s.estado !== "PENDIENTE" ? ` · ${etiqueta("estado_solicitud", s.estado).toLowerCase()} ${formato.haceCuanto(s.actualizado_en)}` : ""}</span>
                </div>
                <div class="solicitud__acciones">
                    ${acciones.map((a) => html`<button type="button" class="boton boton--sm ${ACCIONES[a].clase || ""}" data-accion="${a}" data-id="${s.id}">${ACCIONES[a].texto}</button>`)}
                    <a class="boton boton--secundario boton--sm" href="/solicitudes/${s.id}">Ver detalle</a>
                </div>
            </article>`;
        }

        async function cargar(pagina = 1) {
            const params = new URLSearchParams({ vista, ...(filtroEstado.value ? { estado: filtroEstado.value } : {}) });
            history.replaceState(null, "", `?${params}`);
            pestanas.forEach((p) => p.setAttribute("aria-selected", String(p.dataset.vista === vista)));

            let datos;
            try {
                const consulta = { estado: filtroEstado.value, pagina, tamano: 15 };
                datos = await (vista === "recibidas" ? Api.solicitudes.recibidas(consulta) : Api.solicitudes.enviadas(consulta));
            } catch (error) {
                pintar(contenedor, errorCarga(error));
                return;
            }

            if (!datos.elementos.length) {
                pintar(contenedor, vista === "recibidas"
                    ? vacio({ icono: "📭", titulo: "No tienes solicitudes recibidas", mensaje: "Cuando una empresa solicite uno de tus materiales aparecerá aquí.", accion: html`<a class="boton boton--secundario" href="/mis-materiales">Ver mis materiales</a>` })
                    : vacio({ icono: "📤", titulo: "No has enviado solicitudes", mensaje: "Explora el catálogo y solicita los materiales que te sirven.", accion: html`<a class="boton" href="/materiales">Explorar materiales</a>` }));
                $("#paginacion").innerHTML = "";
                return;
            }
            pintar(contenedor, html`<div class="solicitudes">${datos.elementos.map(tarjeta)}</div>`);
            R.paginacion($("#paginacion"), datos, cargar);

            $$("[data-accion]", contenedor).forEach((boton) =>
                boton.addEventListener("click", async () => {
                    const s = datos.elementos.find((x) => String(x.id) === boton.dataset.id);
                    if (await confirmarAccion(s, boton.dataset.accion)) {
                        cargar(datos.pagina);
                        actualizarPendientes();
                    }
                })
            );
        }

        async function actualizarPendientes() {
            try {
                const { total } = await Api.solicitudes.recibidas({ estado: "PENDIENTE", tamano: 1 });
                $$('[data-total="recibidas"], [data-contador-solicitudes]').forEach((c) => {
                    c.textContent = total;
                    c.hidden = total === 0;
                });
            } catch {
                /* el contador es informativo */
            }
        }

        pestanas.forEach((p) => p.addEventListener("click", () => {
            vista = p.dataset.vista;
            cargar(1);
        }));
        filtroEstado.addEventListener("change", () => cargar(1));
        actualizarPendientes();
        cargar();
    });

    /* -------------------------------------------------- detalle de solicitud */

    R.pagina("solicitud-detalle", async ({ solicitudId }) => {
        const contenedor = $("#solicitud");

        async function mostrar() {
            let s;
            try {
                s = await Api.solicitudes.obtener(solicitudId);
            } catch (error) {
                pintar(contenedor, error.estado === 404 || error.estado === 403
                    ? vacio({ icono: "🔒", titulo: "No puedes ver esta solicitud", mensaje: error.message, accion: html`<a class="boton" href="/solicitudes">Volver a mis solicitudes</a>` })
                    : errorCarga(error));
                return;
            }
            const { soyOfertante } = papel(s);
            const acciones = accionesDisponibles(s);
            const ofertante = s.material.empresa;
            const solicitante = s.empresa_solicitante;
            const miUsuario = R.sesion && R.sesion.id;
            const otraEmpresa = soyOfertante ? solicitante : ofertante;
            document.title = `Solicitud #${s.id} · REVALORA`;

            const resumenMaterial = (m, rotulo) => html`<a class="material-resumen" href="/materiales/${m.id}">
                ${miniatura(m, "miniatura-tabla")}
                <div><span>${rotulo}</span><strong>${m.titulo}</strong><span>${m.categoria.nombre} · ${formato.cantidad(m.cantidad, m.unidad_medida)} disponibles</span></div>
            </a>`;

            pintar(
                contenedor,
                html`<div class="detalle">
                    <div class="pila pila--lg">
                        <div>
                            <div class="fila">${insigniaEstado(s.estado)}<span class="etiqueta">${etiqueta("tipo_solicitud", s.tipo)}</span></div>
                            <h1 style="margin-top:.75rem">${soyOfertante ? `${solicitante.nombre} solicita tu material` : `Solicitaste “${s.material.titulo}”`}</h1>
                            <p class="texto-sm texto-tenue">Enviada el ${formato.fechaHora(s.creado_en)}</p>
                        </div>

                        <dl class="especificaciones" style="margin:0">
                            <div><dt>Cantidad</dt><dd>${formato.cantidad(s.cantidad, s.material.unidad_medida)}</dd></div>
                            ${s.precio_ofrecido != null ? html`<div><dt>Precio ofrecido</dt><dd>${formato.moneda(s.precio_ofrecido)} / ${etiqueta("unidad_corta", s.material.unidad_medida)}</dd></div>` : ""}
                            ${s.tipo === "COMPRA" && s.precio_ofrecido == null && s.material.precio != null ? html`<div><dt>Precio publicado</dt><dd>${formato.moneda(s.material.precio)} / ${etiqueta("unidad_corta", s.material.unidad_medida)}</dd></div>` : ""}
                        </dl>

                        <div class="pila pila--sm">
                            ${resumenMaterial(s.material, "Material solicitado")}
                            ${s.material_ofrecido ? resumenMaterial(s.material_ofrecido, "Ofrecido a cambio") : ""}
                        </div>

                        ${s.mensaje ? html`<div><h2>Mensaje</h2><p class="mensaje-solicitud">${s.mensaje}</p></div>` : ""}

                        <div>
                            <h2>Historial</h2>
                            <ol class="linea-tiempo">
                                ${s.historial.map((h) => html`<li>
                                    <div class="linea-tiempo__cabecera">
                                        ${h.estado_anterior ? html`${insigniaEstado(h.estado_anterior)} →` : ""} ${insigniaEstado(h.estado_nuevo)}
                                        <strong>${h.usuario_id === miUsuario ? "Tú" : otraEmpresa.nombre}</strong>
                                        <span class="linea-tiempo__fecha">${formato.fechaHora(h.creado_en)}</span>
                                    </div>
                                    ${h.comentario && !(h.estado_anterior === null && h.comentario === s.mensaje)
                                        ? html`<p class="linea-tiempo__comentario">“${h.comentario}”</p>` : ""}
                                </li>`)}
                            </ol>
                        </div>
                    </div>

                    <aside class="panel-accion">
                        <div class="tarjeta tarjeta__cuerpo pila">
                            <h3 style="margin:0">Partes</h3>
                            <div class="partes">
                                <div class="parte"><span class="avatar">${formato.iniciales(solicitante.nombre)}</span><div><strong>${solicitante.nombre}</strong><span>Solicita${soyOfertante ? "" : " (tú)"}</span></div></div>
                                <span class="parte__flecha" aria-hidden="true">↓</span>
                                <div class="parte"><span class="avatar">${formato.iniciales(ofertante.nombre)}</span><div><strong>${ofertante.nombre}</strong><span>Ofrece el material${soyOfertante ? " (tú)" : ""}</span></div></div>
                            </div>
                            <a class="boton boton--secundario boton--sm" href="/empresas/${otraEmpresa.id}">Ver datos de contacto de ${otraEmpresa.nombre}</a>
                        </div>
                        <div class="tarjeta tarjeta__cuerpo pila">
                            ${acciones.length
                                ? html`<h3 style="margin:0">${s.estado === "PENDIENTE" ? (soyOfertante ? "Responde a la solicitud" : "Esperando respuesta") : "Siguiente paso"}</h3>
                                    ${s.estado === "PENDIENTE" && !soyOfertante ? html`<p class="texto-sm texto-secundario" style="margin:0">${ofertante.nombre} todavía no responde. Puedes cancelarla mientras siga pendiente.</p>` : ""}
                                    ${s.estado === "ACEPTADA" ? html`<p class="texto-sm texto-secundario" style="margin:0">Coordinen la entrega y márquenla como completada cuando se realice.</p>` : ""}
                                    ${acciones.map((a) => html`<button type="button" class="boton boton--bloque ${ACCIONES[a].clase}" data-accion="${a}">${ACCIONES[a].texto}</button>`)}`
                                : html`<p class="texto-sm texto-secundario" style="margin:0">${s.estado === "COMPLETADA" ? "🎉 Esta operación se completó. ¡Un material menos en la basura!" : "Esta solicitud ya no admite cambios."}</p>`}
                        </div>
                    </aside>
                </div>`
            );

            $$("[data-accion]", contenedor).forEach((boton) =>
                boton.addEventListener("click", async () => {
                    if (await confirmarAccion(s, boton.dataset.accion)) mostrar();
                })
            );
        }

        mostrar();
    });

    /* ------------------------------------------------------------- historial */

    R.pagina("historial", () => {
        const contenedor = $("#historial");
        const miUsuario = R.sesion && R.sesion.id;

        async function cargar(pagina = 1) {
            let datos;
            try {
                datos = await Api.historial.listar({ pagina, tamano: 30 });
            } catch (error) {
                pintar(contenedor, errorCarga(error));
                return;
            }
            if (!datos.elementos.length) {
                pintar(contenedor, vacio({ icono: "🗂️", titulo: "Aún no hay operaciones", mensaje: "Aquí verás cada solicitud enviada, aceptada, rechazada o completada." }));
                return;
            }
            pintar(
                contenedor,
                html`<div class="tarjeta tarjeta__cuerpo"><ol class="linea-tiempo">
                    ${datos.elementos.map((h) => html`<li>
                        <div class="linea-tiempo__cabecera">
                            <a href="/solicitudes/${h.solicitud_id}"><strong>Solicitud #${h.solicitud_id}</strong></a>
                            ${h.estado_anterior ? html`${insigniaEstado(h.estado_anterior)} →` : html`<span class="texto-tenue">creada</span>`} ${insigniaEstado(h.estado_nuevo)}
                            <span class="texto-sm">${h.usuario_id === miUsuario ? "por ti" : "por la otra empresa"}</span>
                        </div>
                        <span class="linea-tiempo__fecha">${formato.fechaHora(h.creado_en)}</span>
                        ${h.comentario ? html`<p class="linea-tiempo__comentario">“${h.comentario}”</p>` : ""}
                    </li>`)}
                </ol></div>`
            );
            R.paginacion($("#paginacion"), datos, cargar);
        }

        cargar();
    });

    window.RevaloraTransaccion = { formularioSolicitud, insigniaEstado };
})();
