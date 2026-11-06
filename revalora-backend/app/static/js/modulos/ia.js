/* REVALORA · módulo ia: componente de reconocimiento del material de una foto.
 *
 * RevaloraIA.reconocimiento(contenedor, opciones) dibuja la zona para subir la
 * foto, la envía a POST /ia/reconocimiento y muestra la categoría sugerida.
 *
 * opciones:
 *   alReconocer(clasificacion)   la IA respondió (ReconocimientoResponse)
 *   alElegirCategoria(id)        el usuario tocó una de las alternativas
 *   alFallar(archivo, error)     la IA no está disponible; el archivo se conserva
 *   alQuitar()                   el usuario descartó la foto
 *   nombreCategoria(id)          (opcional) nombre legible de una categoría
 */

(function () {
    "use strict";

    const { html, crudo, pintar, $, $$, formato, avisar, tamanoMaximoMb } = Revalora;

    const TIPOS_PERMITIDOS = ["image/jpeg", "image/png", "image/webp"];
    const ICONO_CAMARA = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3z"/><circle cx="12" cy="13" r="3"/></svg>';
    const ICONO_CHISPAS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 10.1 8.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3z"/></svg>';

    function validarArchivo(archivo) {
        if (!TIPOS_PERMITIDOS.includes(archivo.type)) return "La foto debe ser JPG, PNG o WEBP.";
        if (archivo.size > tamanoMaximoMb * 1024 * 1024) return `La foto supera los ${tamanoMaximoMb} MB.`;
        return null;
    }

    function reconocimiento(contenedor, opciones = {}) {
        let urlVistaPrevia = null;

        function mostrarZona() {
            pintar(
                contenedor,
                html`<label class="zona-foto">
                    <input type="file" accept="${TIPOS_PERMITIDOS.join(",")}" aria-label="Subir foto del material">
                    <span class="zona-foto__icono">${crudo(ICONO_CAMARA)}</span>
                    <strong>Toma o sube una foto del material</strong>
                    <span class="texto-sm">Arrástrala aquí o haz clic para elegirla</span>
                    <small>JPG, PNG o WEBP · hasta ${tamanoMaximoMb} MB</small>
                </label>`
            );
            const zona = $(".zona-foto", contenedor);
            const entrada = $("input", zona);
            entrada.addEventListener("change", () => entrada.files[0] && procesar(entrada.files[0]));
            ["dragenter", "dragover"].forEach((tipo) =>
                zona.addEventListener(tipo, (e) => {
                    e.preventDefault();
                    zona.classList.add("arrastrando");
                })
            );
            ["dragleave", "drop"].forEach((tipo) => zona.addEventListener(tipo, () => zona.classList.remove("arrastrando")));
            zona.addEventListener("drop", (e) => {
                e.preventDefault();
                const archivo = e.dataTransfer.files[0];
                if (archivo) procesar(archivo);
            });
        }

        function quitar() {
            if (urlVistaPrevia) URL.revokeObjectURL(urlVistaPrevia);
            urlVistaPrevia = null;
            mostrarZona();
            if (opciones.alQuitar) opciones.alQuitar();
        }

        function marco(contenido, analizando = false) {
            pintar(
                contenedor,
                html`<div class="reconocimiento">
                    <div class="reconocimiento__foto ${analizando ? "analizando" : ""}"><img src="${urlVistaPrevia}" alt="Foto del material"></div>
                    <div class="reconocimiento__resultado">${contenido}
                        <div><button type="button" class="boton boton--fantasma boton--sm" data-quitar>Cambiar foto</button></div>
                    </div>
                </div>`
            );
            $("[data-quitar]", contenedor).addEventListener("click", quitar);
        }

        async function procesar(archivo) {
            const problema = validarArchivo(archivo);
            if (problema) {
                avisar(problema, "error");
                return;
            }
            if (urlVistaPrevia) URL.revokeObjectURL(urlVistaPrevia);
            urlVistaPrevia = URL.createObjectURL(archivo);
            marco(html`<p class="reconocimiento__titulo">${crudo(ICONO_CHISPAS)} Analizando la foto…</p>
                <div class="esqueleto" style="height:32px;max-width:220px"></div>
                <div class="esqueleto" style="height:10px;max-width:320px"></div>`, true);

            try {
                const clasificacion = await Api.ia.reconocer(archivo);
                mostrarResultado(clasificacion);
                if (opciones.alReconocer) opciones.alReconocer(clasificacion);
            } catch (error) {
                marco(html`<div class="alerta alerta--aviso"><p><strong>No pudimos reconocer el material.</strong>
                    ${error.message} Puedes continuar: la foto se agregará a la publicación, pero sin verificación con IA.</p></div>`);
                if (opciones.alFallar) opciones.alFallar(archivo, error);
            }
        }

        const nombre = (prediccion) =>
            (opciones.nombreCategoria && opciones.nombreCategoria(prediccion.categoria_id)) || prediccion.material;

        function mostrarResultado(c) {
            const categoria = c.categoria_predicha;
            const alternativas = (c.predicciones || []).filter(
                (p) => p.categoria_id && (!categoria || p.categoria_id !== categoria.id)
            );
            marco(html`<p class="reconocimiento__titulo">${crudo(ICONO_CHISPAS)} La IA reconoce este material como</p>
                <p class="reconocimiento__material">${categoria ? categoria.nombre : c.material_predicho}</p>
                <div class="reconocimiento__confianza">
                    <span>Confianza: <strong>${formato.porcentaje(c.confianza)}</strong></span>
                    <div class="medidor ${c.confianza_baja ? "medidor--bajo" : ""}" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(c.confianza * 100)}">
                        <div class="medidor__barra" style="width:${Math.round(c.confianza * 100)}%"></div>
                    </div>
                </div>
                ${c.confianza_baja ? html`<div class="alerta alerta--aviso"><p>La confianza es baja. Revisa que la categoría sea correcta antes de publicar.</p></div>` : ""}
                ${!categoria ? html`<div class="alerta alerta--info"><p>Este material no corresponde a ninguna categoría de la plataforma. Elige la más cercana.</p></div>` : ""}
                ${alternativas.length ? html`<div class="reconocimiento__alternativas">
                    <span class="texto-xs texto-tenue">¿No es correcto? También podría ser:</span>
                    <div class="chips">${alternativas.map((p) => html`<button type="button" class="chip" data-categoria="${p.categoria_id}">${nombre(p)} · ${formato.porcentaje(p.confianza)}</button>`)}</div>
                </div>` : ""}`);

            $$("[data-categoria]", contenedor).forEach((boton) =>
                boton.addEventListener("click", () => opciones.alElegirCategoria && opciones.alElegirCategoria(Number(boton.dataset.categoria)))
            );
        }

        mostrarZona();
        return { quitar };
    }

    window.RevaloraIA = { reconocimiento, validarArchivo };
})();
