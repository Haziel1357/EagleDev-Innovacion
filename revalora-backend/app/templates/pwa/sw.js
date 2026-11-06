/* =============================================================================
   REVALORA · service worker (lo sirve pwa_controller en /sw.js)
   - Páginas: siempre desde la red; sin conexión se muestra /sin-conexion. No se
     guardan porque llevan los datos de la sesión del usuario.
   - /static: primero la red (nunca se ven estilos ni scripts viejos) y, sin
     conexión, la última copia guardada.
   - Google Fonts: primero la caché (sus archivos no cambian).
   - La API (/api/v1) y las fotos subidas no pasan por aquí: van directo a la red.
   ========================================================================== */

const VERSION = {{ version | tojson }};
const CACHE_APP = `revalora-app-${VERSION}`;
const CACHE_FUENTES = "revalora-fuentes";
const URL_SIN_CONEXION = {{ url_sin_conexion | tojson }};
const PREFIJO_ESTATICOS = {{ prefijo_estaticos | tojson }};
const PRECACHE = {{ precache | tojson }};
const ORIGENES_FUENTES = ["https://fonts.googleapis.com", "https://fonts.gstatic.com"];

self.addEventListener("install", (evento) => {
    evento.waitUntil(
        caches
            .open(CACHE_APP)
            // "reload": copias nuevas aunque el navegador tenga otras en su caché HTTP.
            .then((cache) => cache.addAll(PRECACHE.map((url) => new Request(url, { cache: "reload" }))))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener("activate", (evento) => {
    evento.waitUntil(
        (async () => {
            const vigentes = [CACHE_APP, CACHE_FUENTES];
            const nombres = await caches.keys();
            await Promise.all(
                nombres
                    .filter((nombre) => nombre.startsWith("revalora-") && !vigentes.includes(nombre))
                    .map((nombre) => caches.delete(nombre))
            );
            // Pide la página a la red mientras el service worker arranca.
            if (self.registration.navigationPreload) await self.registration.navigationPreload.enable();
            await self.clients.claim();
        })()
    );
});

async function navegar(evento) {
    try {
        return (await evento.preloadResponse) || (await fetch(evento.request));
    } catch {
        return (await caches.match(URL_SIN_CONEXION)) || Response.error();
    }
}

async function redPrimero(evento) {
    const cache = await caches.open(CACHE_APP);
    try {
        const respuesta = await fetch(evento.request);
        if (respuesta.ok) evento.waitUntil(cache.put(evento.request, respuesta.clone()));
        return respuesta;
    } catch (error) {
        const guardada = await cache.match(evento.request);
        if (guardada) return guardada;
        throw error;
    }
}

async function cachePrimero(evento) {
    const cache = await caches.open(CACHE_FUENTES);
    const guardada = await cache.match(evento.request);
    if (guardada) return guardada;
    const respuesta = await fetch(evento.request);
    // La hoja de estilos de Google llega "opaca" (se pide sin CORS): se guarda igual.
    if (respuesta.ok || respuesta.type === "opaque") {
        evento.waitUntil(cache.put(evento.request, respuesta.clone()));
    }
    return respuesta;
}

self.addEventListener("fetch", (evento) => {
    const { request } = evento;
    if (request.method !== "GET") return;
    const url = new URL(request.url);

    if (request.mode === "navigate") {
        evento.respondWith(navegar(evento));
    } else if (url.origin === self.location.origin && url.pathname.startsWith(PREFIJO_ESTATICOS)) {
        evento.respondWith(redPrimero(evento));
    } else if (ORIGENES_FUENTES.includes(url.origin)) {
        evento.respondWith(cachePrimero(evento));
    }
});
