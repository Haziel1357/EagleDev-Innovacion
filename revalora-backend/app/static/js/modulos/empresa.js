/* REVALORA · módulo empresa: registro, edición y perfil público. */

(function () {
    "use strict";

    const { $, html, pintar, pagina, manejarFormulario, rellenarFormulario, irA, parametrosUrl, rutaSegura,
        avisar, conCarga, obtenerUbicacion, etiqueta, formato, errorCarga } = Revalora;

    pagina("empresa-formulario", async ({ empresaId }) => {
        const formulario = $("#formulario-empresa");
        const selectActividad = $("#actividad_economica_id");

        const [actividades, empresa] = await Promise.all([
            Api.empresas.actividades(),
            empresaId ? Api.empresas.mia() : null,
        ]);
        actividades.forEach((a) => selectActividad.add(new Option(`${a.codigo} · ${a.nombre}`, a.id)));

        if (empresa) {
            rellenarFormulario(formulario, {
                ...empresa,
                actividad_economica_id: empresa.actividad_economica ? empresa.actividad_economica.id : "",
            });
        }

        const botonUbicacion = $("#usar-ubicacion");
        botonUbicacion.addEventListener("click", () =>
            conCarga(botonUbicacion, async () => {
                try {
                    const { latitud, longitud } = await obtenerUbicacion();
                    $("#latitud").value = latitud;
                    $("#longitud").value = longitud;
                    avisar("Ubicación agregada.", "info", 2500);
                } catch (error) {
                    avisar(error.message, "aviso");
                }
            })
        );

        manejarFormulario(formulario, async (datos) => {
            if (empresa) {
                await Api.empresas.actualizar(empresa.id, datos);
                avisar("Los datos de tu empresa se guardaron.");
            } else {
                await Api.empresas.registrar(datos);
                const destino = rutaSegura(parametrosUrl().siguiente, "/materiales/publicar");
                irA(destino, "¡Empresa registrada! Ya puedes publicar tus materiales sobrantes.");
            }
        });
    });

    pagina("empresa-detalle", async ({ empresaId }) => {
        const contenedor = $("#empresa");
        let empresa;
        try {
            empresa = await Api.empresas.obtener(empresaId);
        } catch (error) {
            pintar(contenedor, errorCarga(error));
            return;
        }
        document.title = `${empresa.nombre} · REVALORA`;
        const u = empresa.ubicacion;
        const lugar = [u.ciudad, u.region, u.pais].filter(Boolean).join(", ");

        pintar(
            contenedor,
            html`<article class="tarjeta empresa-perfil">
                <div class="empresa-perfil__portada"></div>
                <div class="empresa-perfil__cuerpo">
                    <div class="empresa-perfil__avatar" aria-hidden="true">${formato.iniciales(empresa.nombre)}</div>
                    <h1>${empresa.nombre}</h1>
                    <div class="fila">
                        <span class="etiqueta etiqueta--verde">${etiqueta("tipo_empresa", empresa.tipo)}</span>
                        <span class="etiqueta">📍 ${lugar}</span>
                        ${empresa.actividad_economica ? html`<span class="etiqueta">${empresa.actividad_economica.nombre}</span>` : ""}
                    </div>
                    ${empresa.descripcion ? html`<p class="texto-secundario" style="margin-top:1rem">${empresa.descripcion}</p>` : ""}
                    <dl class="datos-lista">
                        ${empresa.telefono ? html`<div><dt>Teléfono</dt><dd><a href="tel:${empresa.telefono}">${empresa.telefono}</a></dd></div>` : ""}
                        ${empresa.email ? html`<div><dt>Correo</dt><dd><a href="mailto:${empresa.email}">${empresa.email}</a></dd></div>` : ""}
                        ${u.direccion ? html`<div><dt>Dirección</dt><dd>${u.direccion}</dd></div>` : ""}
                        <div><dt>En REVALORA desde</dt><dd>${formato.fecha(empresa.creado_en)}</dd></div>
                    </dl>
                </div>
            </article>`
        );
    });
})();
