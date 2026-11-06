/* REVALORA · módulo usuario: ingreso, registro y perfil. */

(function () {
    "use strict";

    const { $, pagina, manejarFormulario, irA, parametrosUrl, rutaSegura, avisar, limpiarErrores } = Revalora;

    pagina("ingresar", () => {
        const destino = rutaSegura(parametrosUrl().siguiente, "/app/materiales");
        manejarFormulario($("#formulario-ingreso"), async (datos) => {
            const { usuario } = await Api.auth.login(datos);
            irA(destino, `¡Hola, ${usuario.nombre.split(" ")[0]}!`);
        });
    });

    pagina("registro", () => {
        manejarFormulario($("#formulario-registro"), async (datos) => {
            await Api.auth.registro(datos);
            irA("/app/empresa", "Cuenta creada. Ahora registra los datos de tu empresa.");
        });
    });

    pagina("perfil", () => {
        manejarFormulario($("#formulario-perfil"), async (datos) => {
            await Api.usuarios.actualizarme({ nombre: datos.nombre, telefono: datos.telefono ?? null });
            avisar("Tus datos se actualizaron.");
        });

        const formularioContrasena = $("#formulario-contrasena");
        manejarFormulario(formularioContrasena, async (datos) => {
            await Api.usuarios.actualizarme(datos);
            formularioContrasena.reset();
            limpiarErrores(formularioContrasena);
            avisar("Tu contraseña se actualizó.");
        });
    });
})();
