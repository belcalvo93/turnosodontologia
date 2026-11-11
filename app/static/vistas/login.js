/**
 * Vista de inicio de sesión (`#login`, `POST /auth/login`, tarea 3.2 de C-18).
 * Autentica al usuario, almacena el `access_token` en `sessionStorage` y muestra
 * el `mensaje` en español devuelto por la API ante `401 credenciales_invalidas` (`RN-ACC-01`, `RN-GLO-01`).
 */
import { ErrorClienteApi, iniciarSesion, interpretarErrorApi } from "../api.js";
import { guardarToken } from "../auth.js";
function obtenerElemento(id) {
    if (typeof document === "undefined") {
        return null;
    }
    return document.getElementById(id);
}
/**
 * Muestra el contenedor `#login-error` con el mensaje en español proveniente de la API (`RN-GLO-01`).
 */
export function mostrarErrorLogin(mensaje) {
    const contenedor = obtenerElemento("login-error");
    const parrafo = obtenerElemento("login-error-mensaje");
    if (parrafo !== null) {
        parrafo.removeAttribute("data-ejemplo");
        parrafo.textContent = mensaje;
    }
    if (contenedor !== null) {
        contenedor.hidden = false;
    }
}
/**
 * Oculta el contenedor `#login-error`.
 */
export function ocultarErrorLogin() {
    const contenedor = obtenerElemento("login-error");
    const parrafo = obtenerElemento("login-error-mensaje");
    if (parrafo !== null) {
        parrafo.removeAttribute("data-ejemplo");
        parrafo.textContent = "";
    }
    if (contenedor !== null) {
        contenedor.hidden = true;
    }
}
function limpiarAtributosEjemploLogin() {
    if (typeof document === "undefined") {
        return;
    }
    const seccionLogin = document.getElementById("login");
    if (seccionLogin === null) {
        return;
    }
    for (const elem of seccionLogin.querySelectorAll("[data-ejemplo]")) {
        elem.removeAttribute("data-ejemplo");
    }
}
/**
 * Inicializa el formulario `#form-login` y los chips de usuarios de prueba.
 */
export function inicializarVistaLogin(opciones = {}) {
    limpiarAtributosEjemploLogin();
    ocultarErrorLogin();
    const formulario = obtenerElemento("form-login");
    const inputUsername = obtenerElemento("login-username");
    const inputPassword = obtenerElemento("login-password");
    const botonSubmit = obtenerElemento("btn-login-submit");
    if (typeof document !== "undefined") {
        const chipsDemo = document.querySelectorAll(".demo-role-chip code");
        for (const codigo of chipsDemo) {
            const chip = codigo.closest(".demo-role-chip");
            if (chip !== null && inputUsername !== null) {
                chip.addEventListener("click", () => {
                    inputUsername.value = (codigo.textContent ?? "").trim();
                    inputPassword?.focus();
                });
            }
        }
    }
    if (formulario === null || inputUsername === null || inputPassword === null) {
        return;
    }
    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        ocultarErrorLogin();
        const username = inputUsername.value.trim();
        const password = inputPassword.value;
        if (botonSubmit !== null) {
            botonSubmit.disabled = true;
            botonSubmit.classList.add("is-loading");
        }
        try {
            const respuesta = await iniciarSesion({ username, password });
            const payload = guardarToken(respuesta.access_token, username);
            if (payload === null) {
                mostrarErrorLogin("El token recibido no tiene un formato válido.");
                return;
            }
            inputPassword.value = "";
            if (opciones.alAutenticar !== undefined) {
                await opciones.alAutenticar(payload, username);
            }
        }
        catch (error) {
            if (error instanceof ErrorClienteApi) {
                mostrarErrorLogin(error.mensaje);
            }
            else {
                const interpretado = interpretarErrorApi(error);
                mostrarErrorLogin(interpretado.mensaje);
            }
        }
        finally {
            if (botonSubmit !== null) {
                botonSubmit.disabled = false;
                botonSubmit.classList.remove("is-loading");
            }
        }
    });
}
export const montarVistaLogin = inicializarVistaLogin;
export const initLogin = inicializarVistaLogin;
