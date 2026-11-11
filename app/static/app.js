/**
 * Punto de entrada del frontend mínimo de Turnos Odontológicos (C-18, tarea 3.2).
 * Conecta las vistas y maneja la navegación RBAC (`RN-ACC-01`, `RN-ACC-02`, `RN-GLO-01`).
 */
import { registrarManejadorNoAutenticado } from "./api.js";
import { ETIQUETAS_ROL, limpiarSesion, obtenerRolActual, obtenerSesionActual, puedeVerVista, tieneSesionValida, vistasPermitidasPorRol, } from "./auth.js";
import { cargarVistaAgenda, inicializarVistaAgenda } from "./vistas/agenda.js";
import { inicializarVistaLogin, mostrarErrorLogin, ocultarErrorLogin, } from "./vistas/login.js";
export const VERSION_FRONTEND = "0.1.0";
const TODAS_LAS_VISTAS = [
    "login",
    "agenda",
    "crear-turno",
    "crear-bloqueo",
];
const BOTONES_NAVEGACION = {
    agenda: "nav-agenda",
    "crear-turno": "nav-crear-turno",
    "crear-bloqueo": "nav-crear-bloqueo",
};
const vistasOpcionalesInicializadas = new Set();
const MENSAJE_VISTA_NO_CARGADA = "No se pudo cargar la pantalla. Recargá la página.";
function obtenerElemento(id) {
    if (typeof document === "undefined") {
        return null;
    }
    return document.getElementById(id);
}
/**
 * Muestra la alerta transversal `#alerta-global` con el mensaje (y detalles opcionales) en español (`RN-GLO-01`).
 */
export function mostrarAlertaGlobal(mensaje, detalles = [], titulo = "No se pudo completar la operación") {
    const alerta = obtenerElemento("alerta-global");
    const elemTitulo = obtenerElemento("alerta-titulo");
    const elemMensaje = obtenerElemento("alerta-mensaje");
    const listaDetalles = obtenerElemento("alerta-detalles");
    if (elemTitulo !== null) {
        elemTitulo.removeAttribute("data-ejemplo");
        elemTitulo.textContent = titulo;
    }
    if (elemMensaje !== null) {
        elemMensaje.removeAttribute("data-ejemplo");
        elemMensaje.textContent = mensaje;
    }
    if (listaDetalles !== null) {
        listaDetalles.replaceChildren();
        if (detalles.length > 0) {
            for (const d of detalles) {
                const li = document.createElement("li");
                li.textContent = `${d.campo}: ${d.mensaje}`;
                listaDetalles.appendChild(li);
            }
            listaDetalles.hidden = false;
        }
        else {
            listaDetalles.hidden = true;
        }
    }
    if (alerta !== null) {
        alerta.hidden = false;
    }
}
/**
 * Oculta la alerta transversal `#alerta-global`.
 */
export function ocultarAlertaGlobal() {
    const alerta = obtenerElemento("alerta-global");
    const listaDetalles = obtenerElemento("alerta-detalles");
    if (listaDetalles !== null) {
        listaDetalles.replaceChildren();
        listaDetalles.hidden = true;
    }
    if (alerta !== null) {
        alerta.hidden = true;
    }
}
/**
 * Actualiza la barra superior `#barra-navegacion` según el rol autenticado (`RN-ACC-02`):
 * - `administracion`: Agenda + Crear Turno + Crear Bloqueo
 * - `recepcion`: Agenda + Crear Turno
 * - `odontologo`: solo Agenda
 * - `null`: oculta toda la barra de navegación
 */
export function aplicarNavegacionPorRol(rol, username) {
    const barra = obtenerElemento("barra-navegacion");
    const spanUsuario = obtenerElemento("sesion-usuario");
    const spanRol = obtenerElemento("sesion-rol");
    if (rol === null) {
        if (barra !== null) {
            barra.hidden = true;
        }
        return;
    }
    const permitidas = new Set(vistasPermitidasPorRol(rol));
    for (const [vista, botonId] of Object.entries(BOTONES_NAVEGACION)) {
        const boton = obtenerElemento(botonId);
        if (boton !== null) {
            boton.hidden = !permitidas.has(vista);
        }
    }
    if (spanUsuario !== null) {
        spanUsuario.removeAttribute("data-ejemplo");
        spanUsuario.textContent =
            username && username.trim().length > 0 ? username.trim() : rol;
    }
    if (spanRol !== null) {
        spanRol.removeAttribute("data-ejemplo");
        spanRol.textContent = ETIQUETAS_ROL[rol];
    }
    if (barra !== null) {
        barra.hidden = false;
    }
}
async function activarVistaOpcional(vista) {
    const rutaModulo = vista === "crear-turno"
        ? "./vistas/crear-turno.js"
        : "./vistas/crear-bloqueo.js";
    try {
        const modulo = (await import(rutaModulo));
        if (!vistasOpcionalesInicializadas.has(vista)) {
            const fnInit = vista === "crear-turno"
                ? modulo.inicializarVistaCrearTurno ??
                    modulo.montarVistaCrearTurno ??
                    modulo.initCrearTurno ??
                    modulo.default
                : modulo.inicializarVistaCrearBloqueo ??
                    modulo.montarVistaCrearBloqueo ??
                    modulo.initCrearBloqueo ??
                    modulo.default;
            if (typeof fnInit === "function") {
                await fnInit();
            }
            vistasOpcionalesInicializadas.add(vista);
        }
        const fnRefrescar = vista === "crear-turno"
            ? modulo.cargarVistaCrearTurno ?? modulo.refrescarCrearTurno
            : modulo.cargarVistaCrearBloqueo ?? modulo.refrescarCrearBloqueo;
        if (typeof fnRefrescar === "function") {
            await fnRefrescar();
        }
    }
    catch (error) {
        // Si el módulo de la vista no carga, se avisa en pantalla en lugar de dejarla en blanco.
        console.error(error);
        mostrarAlertaGlobal(MENSAJE_VISTA_NO_CARGADA);
    }
}
/**
 * Conmuta la vista activa verificando los permisos del rol actual (`RN-ACC-02`).
 */
export async function mostrarVista(vistaSolicitada) {
    ocultarAlertaGlobal();
    const rol = obtenerRolActual();
    const destino = rol === null || !puedeVerVista(rol, vistaSolicitada)
        ? rol === null
            ? "login"
            : "agenda"
        : vistaSolicitada;
    for (const id of TODAS_LAS_VISTAS) {
        const seccion = obtenerElemento(id);
        if (seccion !== null) {
            seccion.hidden = id !== destino;
        }
    }
    for (const [vista, botonId] of Object.entries(BOTONES_NAVEGACION)) {
        const boton = obtenerElemento(botonId);
        if (boton !== null) {
            const activa = vista === destino;
            boton.classList.toggle("is-active", activa);
            if (activa) {
                boton.setAttribute("aria-current", "page");
            }
            else {
                boton.removeAttribute("aria-current");
            }
        }
    }
    if (destino === "agenda") {
        await cargarVistaAgenda();
    }
    else if (destino === "crear-turno" || destino === "crear-bloqueo") {
        await activarVistaOpcional(destino);
    }
}
function redirigirAlLoginPorSesionInvalida(mensaje) {
    limpiarSesion();
    aplicarNavegacionPorRol(null);
    for (const id of TODAS_LAS_VISTAS) {
        const seccion = obtenerElemento(id);
        if (seccion !== null) {
            seccion.hidden = id !== "login";
        }
    }
    if (mensaje && mensaje.trim().length > 0) {
        mostrarErrorLogin(mensaje);
        mostrarAlertaGlobal(mensaje, [], "Sesión finalizada");
    }
    else {
        ocultarErrorLogin();
        ocultarAlertaGlobal();
    }
}
/**
 * Inicializa la aplicación en el navegador, conectando el login, la barra RBAC y las vistas.
 */
export function inicializarApp() {
    if (typeof document === "undefined") {
        return;
    }
    const botonCerrarAlerta = obtenerElemento("btn-cerrar-alerta");
    if (botonCerrarAlerta !== null) {
        botonCerrarAlerta.addEventListener("click", () => {
            ocultarAlertaGlobal();
        });
    }
    const botonCerrarSesion = obtenerElemento("btn-cerrar-sesion");
    if (botonCerrarSesion !== null) {
        botonCerrarSesion.addEventListener("click", () => {
            redirigirAlLoginPorSesionInvalida();
        });
    }
    for (const [vista, botonId] of Object.entries(BOTONES_NAVEGACION)) {
        const boton = obtenerElemento(botonId);
        if (boton !== null) {
            boton.addEventListener("click", () => {
                void mostrarVista(vista);
            });
        }
    }
    registrarManejadorNoAutenticado((error) => {
        redirigirAlLoginPorSesionInvalida(error.mensaje);
    });
    inicializarVistaAgenda();
    inicializarVistaLogin({
        alAutenticar: async (payload, username) => {
            ocultarAlertaGlobal();
            aplicarNavegacionPorRol(payload.rol, username);
            await mostrarVista("agenda");
        },
    });
    if (tieneSesionValida()) {
        const sesion = obtenerSesionActual();
        if (sesion !== null) {
            aplicarNavegacionPorRol(sesion.rol, sesion.username ?? sesion.sub);
            void mostrarVista("agenda");
            return;
        }
    }
    redirigirAlLoginPorSesionInvalida();
}
if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            inicializarApp();
        });
    }
    else {
        inicializarApp();
    }
}
