/* =============================================================================
   REVALORA · aplicación web progresiva (PWA)
   - Registra el service worker (/sw.js, plantilla templates/pwa/sw.js).
   - Muestra los botones «Instalar app» ([data-instalar-app]) cuando el
     navegador permite instalarla (Chrome, Edge y Android; en iOS se instala
     desde Compartir → Agregar a inicio).
   - Avisa cuando se pierde y se recupera la conexión.
   ========================================================================== */

(function () {
    "use strict";

    const { $$, avisar } = window.Revalora;
    const URL_SERVICE_WORKER = (window.REVALORA && window.REVALORA.serviceWorker) || "/sw.js";

    /* -------------------------------------------------------- service worker */

    // Solo existe en contextos seguros: HTTPS o localhost.
    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker.register(URL_SERVICE_WORKER).catch((error) => {
                console.error("No se pudo registrar el service worker.", error);
            });
        });
    }

    /* ------------------------------------------------------------- instalar */

    let solicitudInstalacion = null;

    function mostrarInstalar(visible) {
        $$("[data-instalar-app]").forEach((elemento) => {
            elemento.hidden = !visible;
        });
    }

    window.addEventListener("beforeinstallprompt", (evento) => {
        // Se guarda para lanzarlo desde nuestro botón en lugar del aviso del navegador.
        evento.preventDefault();
        solicitudInstalacion = evento;
        mostrarInstalar(true);
    });

    $$("[data-instalar-app]").forEach((elemento) =>
        elemento.addEventListener("click", () => {
            if (!solicitudInstalacion) return;
            // Cada solicitud se puede mostrar una sola vez.
            solicitudInstalacion.prompt();
            solicitudInstalacion = null;
            mostrarInstalar(false);
        })
    );

    window.addEventListener("appinstalled", () => {
        solicitudInstalacion = null;
        mostrarInstalar(false);
        avisar("REVALORA quedó instalada en tu dispositivo.");
    });

    /* ------------------------------------------------------------- conexión */

    let avisoSinConexion = null;

    window.addEventListener("offline", () => {
        avisoSinConexion = avisar(
            "Estás sin conexión. Podrás seguir viendo esta página, pero no guardar cambios hasta que vuelvas a conectarte.",
            "aviso",
            0
        );
    });

    window.addEventListener("online", () => {
        if (avisoSinConexion) avisoSinConexion.remove();
        avisoSinConexion = null;
        avisar("Conexión restablecida.", "info");
    });
})();
