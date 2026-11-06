/* REVALORA · módulo oportunidad: análisis con IA de productos que la empresa
 * puede fabricar con sus materiales y de los materiales que le faltan. */

(function () {
    "use strict";

    const R = Revalora;
    const { $, $$, html, pintar, formato, visualCategoria, irA, vacio, errorCarga } = R;

    let categoriasCache = null;
    const categorias = () => (categoriasCache = categoriasCache || Api.categorias.listar());

    /** Los materiales llegan como códigos ("madera"); se muestran con su nombre. */
    async function nombres() {
        const lista = await categorias();
        const mapa = Object.fromEntries(lista.map((c) => [c.codigo, c.nombre]));
        return (codigo) => mapa[codigo] || codigo;
    }

    const chipMaterial = (codigo, nombre) => html`<span class="etiqueta">${visualCategoria(codigo)[0]} ${nombre(codigo)}</span>`;

    /* ------------------------------------------------------------------ lista */

    R.pagina("oportunidades", async () => {
        const formulario = $("#formulario-analisis");
        const chips = $("#categorias-analisis");
        const contenedor = $("#oportunidades");
        const seleccion = new Set();
        const [lista, nombre] = await Promise.all([categorias(), nombres()]);

        pintar(chips, lista.map((c) => html`<button type="button" class="chip" data-id="${c.id}" aria-pressed="false">${visualCategoria(c.codigo)[0]} ${c.nombre}</button>`));
        $$(".chip", chips).forEach((chip) =>
            chip.addEventListener("click", () => {
                const id = Number(chip.dataset.id);
                if (seleccion.has(id)) seleccion.delete(id);
                else seleccion.add(id);
                chip.setAttribute("aria-pressed", String(seleccion.has(id)));
            })
        );

        R.manejarFormulario(formulario, async (datos) => {
            const oportunidad = await Api.oportunidades.analizar({
                max_productos: datos.max_productos,
                categoria_ids: seleccion.size ? [...seleccion] : null,
            });
            irA(`/oportunidades/${oportunidad.id}`, oportunidad.productos.length ? "¡Análisis listo!" : "La IA no encontró productos para estos materiales.", oportunidad.productos.length ? "exito" : "info");
        });

        async function cargar(pagina = 1) {
            let datos;
            try {
                datos = await Api.oportunidades.listar({ pagina, tamano: 12 });
            } catch (error) {
                pintar(contenedor, errorCarga(error));
                return;
            }
            if (!datos.elementos.length) {
                pintar(contenedor, vacio({ icono: "💡", titulo: "Aún no has hecho análisis", mensaje: "Lanza el primero: la IA te sugerirá productos para tus sobrantes." }));
                return;
            }
            pintar(
                contenedor,
                html`<div class="analisis-anteriores">${datos.elementos.map((o) => html`<a class="analisis-tarjeta" href="/oportunidades/${o.id}">
                    <span>${formato.fechaHora(o.creado_en)}</span>
                    <strong>${o.productos.length ? o.productos.map((p) => p.nombre).slice(0, 2).join(", ") + (o.productos.length > 2 ? "…" : "") : "Sin productos sugeridos"}</strong>
                    <div class="chips">${o.materiales_analizados.map((m) => chipMaterial(m, nombre))}</div>
                    <span>${o.productos.length} ${o.productos.length === 1 ? "producto" : "productos"} sugeridos</span>
                </a>`)}</div>`
            );
            R.paginacion($("#paginacion"), datos, cargar);
        }
        cargar();
    });

    /* ---------------------------------------------------------------- detalle */

    R.pagina("oportunidad-detalle", async ({ oportunidadId }) => {
        const contenedor = $("#oportunidad");
        let o;
        try {
            o = await Api.oportunidades.obtener(oportunidadId);
        } catch (error) {
            pintar(contenedor, errorCarga(error));
            return;
        }
        const nombre = await nombres();
        const productos = [...o.productos].sort((a, b) => b.viabilidad - a.viabilidad);

        const faltante = (f) => html`<li class="faltante">
            <span>${visualCategoria(f.categoria ? f.categoria.codigo : "otro")[0]} <strong>${f.categoria ? f.categoria.nombre : f.material}</strong>
                ${f.descripcion ? html`<small>${f.descripcion}</small>` : ""}</span>
            ${f.categoria
                ? f.disponibles_en_plataforma
                    ? html`<a class="boton boton--secundario boton--sm" href="/materiales?categoria_id=${f.categoria.id}">Ver ${f.disponibles_en_plataforma} disponibles</a>`
                    : html`<a class="boton boton--fantasma boton--sm" href="/necesidades/publicar?categoria_id=${f.categoria.id}">Publicar necesidad</a>`
                : html`<span class="texto-xs texto-tenue">No está en la plataforma</span>`}
        </li>`;

        pintar(
            contenedor,
            html`<div class="pagina__cabecera">
                <div>
                    <h1>Lo que puedes fabricar</h1>
                    <p>Análisis del ${formato.fechaHora(o.creado_en)} con estos materiales:</p>
                    <div class="chips" style="margin-top:.5rem">${o.materiales_analizados.map((m) => chipMaterial(m, nombre))}</div>
                </div>
                <a class="boton boton--secundario" href="/oportunidades">Nuevo análisis</a>
            </div>
            ${productos.length
                ? html`<div class="productos">${productos.map((p) => html`<article class="producto">
                    <div class="producto__cabecera">
                        <h3>${p.nombre}</h3>
                        <span class="etiqueta ${p.viabilidad >= 0.7 ? "etiqueta--verde" : p.viabilidad >= 0.4 ? "etiqueta--aviso" : ""}">${formato.porcentaje(p.viabilidad)} viable</span>
                    </div>
                    <div class="producto__viabilidad">
                        <div class="medidor ${p.viabilidad < 0.5 ? "medidor--bajo" : ""}"><span class="medidor__barra" style="width:${Math.round(p.viabilidad * 100)}%"></span></div>
                    </div>
                    ${p.descripcion ? html`<p class="texto-sm texto-secundario" style="margin:0">${p.descripcion}</p>` : ""}
                    ${p.materiales_utilizados.length ? html`<div class="producto__bloque"><h4>Usa tus materiales</h4>
                        <div class="chips">${p.materiales_utilizados.map((m) => chipMaterial(m, nombre))}</div></div>` : ""}
                    <div class="producto__bloque"><h4>${p.materiales_faltantes.length ? "Te falta" : "Tienes todo lo necesario"}</h4>
                        ${p.materiales_faltantes.length ? html`<ul class="faltantes">${p.materiales_faltantes.map(faltante)}</ul>` : html`<span class="etiqueta etiqueta--verde">✔ Puedes fabricarlo ya</span>`}
                    </div>
                </article>`)}</div>`
                : vacio({ icono: "🤔", titulo: "La IA no encontró productos", mensaje: "Prueba con otras categorías o publica más materiales." })}`
        );
    });
})();
