/**
 * Cliente HTTP del frontend mínimo (C-18, D3, D4, D5, RN-ACC-01, RN-GLO-01).
 * Adjunta `Authorization: Bearer <token>`, normaliza fechas locales (`NaiveDatetime`),
 * limpia `sessionStorage` ante `401` (`no_autenticado`) y extrae `mensaje` y `detalles` en español.
 */
import { limpiarSesion, obtenerToken } from "./auth.js";
import { filtrarActivos, formatearPacienteId, formatearPacienteOdontologo, interpretarErrorApi, normalizarFechaLocal, } from "./logica.js";
export { filtrarActivos, formatearPacienteId, formatearPacienteOdontologo, interpretarErrorApi, normalizarFechaLocal, };
/**
 * Error estructurado devuelto por la API con su código HTTP y textos en español (`RN-GLO-01`).
 */
export class ErrorClienteApi extends Error {
    status;
    codigo;
    mensaje;
    detalles;
    constructor(status, interpretado) {
        super(interpretado.mensaje);
        this.name = "ErrorClienteApi";
        this.status = status;
        this.codigo = interpretado.codigo;
        this.mensaje = interpretado.mensaje;
        this.detalles = interpretado.detalles;
    }
}
export { ErrorClienteApi as ErrorApi };
let manejadorNoAutenticado = null;
/**
 * Registra un callback que se invoca automáticamente cuando una ruta protegida
 * responde `401` (`no_autenticado`), tras haber limpiado `sessionStorage`.
 */
export function registrarManejadorNoAutenticado(manejador) {
    manejadorNoAutenticado = manejador;
}
export const alExpirarSesion = registrarManejadorNoAutenticado;
/**
 * Ejecuta una petición `fetch` contra el mismo origen de la API FastAPI:
 * - Adjunta `Authorization: Bearer <token>` cuando `autenticado !== false` y hay token en `sessionStorage`.
 * - Ante `401` (`no_autenticado`), limpia `sessionStorage` y notifica a la interfaz para volver al login.
 * - Ante cualquier status `>= 400`, extrae `codigo`, `mensaje` y `detalles` en español y lanza `ErrorClienteApi`.
 */
export async function peticionApi(ruta, opciones = {}) {
    const { body, autenticado = true, headers: cabecerasExtra, ...resto } = opciones;
    const cabeceras = new Headers(cabecerasExtra);
    if (!cabeceras.has("Accept")) {
        cabeceras.set("Accept", "application/json");
    }
    let cuerpoSerializado;
    if (body !== undefined) {
        if (typeof body === "string" || body instanceof FormData || body instanceof URLSearchParams) {
            cuerpoSerializado = body;
        }
        else {
            if (!cabeceras.has("Content-Type")) {
                cabeceras.set("Content-Type", "application/json");
            }
            cuerpoSerializado = JSON.stringify(body);
        }
    }
    if (autenticado) {
        const token = obtenerToken();
        if (token !== null && token.length > 0 && !cabeceras.has("Authorization")) {
            cabeceras.set("Authorization", `Bearer ${token}`);
        }
    }
    const respuesta = await fetch(ruta, {
        ...resto,
        headers: cabeceras,
        body: cuerpoSerializado,
    });
    if (!respuesta.ok) {
        let cuerpoError = null;
        try {
            cuerpoError = await respuesta.json();
        }
        catch {
            cuerpoError = null;
        }
        const interpretado = interpretarErrorApi(cuerpoError);
        const errorCliente = new ErrorClienteApi(respuesta.status, interpretado);
        if (respuesta.status === 401 &&
            (interpretado.codigo === "no_autenticado" || autenticado)) {
            limpiarSesion();
            if (manejadorNoAutenticado !== null) {
                manejadorNoAutenticado(errorCliente);
            }
            if (typeof window !== "undefined" && typeof CustomEvent !== "undefined") {
                window.dispatchEvent(new CustomEvent("sesion-expirada", { detail: errorCliente }));
            }
        }
        throw errorCliente;
    }
    if (respuesta.status === 204) {
        return undefined;
    }
    return (await respuesta.json());
}
export const fetchApi = peticionApi;
export const solicitarApi = peticionApi;
/**
 * Autentica al usuario contra `POST /auth/login` (`RN-ACC-01`).
 * Ante `401 credenciales_invalidas`, lanza `ErrorClienteApi` con el `mensaje` en español de la API.
 */
export async function iniciarSesion(credenciales) {
    return peticionApi("/auth/login", {
        method: "POST",
        body: credenciales,
        autenticado: false,
    });
}
export const login = iniciarSesion;
/**
 * Obtiene el catálogo completo de profesionales (`GET /profesionales`).
 */
export async function listarProfesionales() {
    return peticionApi("/profesionales", { method: "GET" });
}
export const obtenerProfesionales = listarProfesionales;
/**
 * Obtiene el catálogo completo de sillones (`GET /sillones`).
 */
export async function listarSillones() {
    return peticionApi("/sillones", { method: "GET" });
}
export const obtenerSillones = listarSillones;
/**
 * Obtiene el catálogo completo de prestaciones (`GET /prestaciones`).
 */
export async function listarPrestaciones() {
    return peticionApi("/prestaciones", { method: "GET" });
}
export const obtenerPrestaciones = listarPrestaciones;
/**
 * Obtiene el catálogo de pacientes ficticios (`GET /pacientes`, permitido a `administracion` y `recepcion`).
 */
export async function listarPacientes() {
    return peticionApi("/pacientes", { method: "GET" });
}
export const obtenerPacientes = listarPacientes;
/**
 * Consulta la agenda de un profesional en el rango `[desde, hasta)` (`GET /agenda/profesionales/{id}`).
 * Normaliza automáticamente `desde` y `hasta` a `YYYY-MM-DDTHH:MM:00` (`NaiveDatetime`).
 */
export async function consultarAgendaProfesional(profesionalId, desde, hasta) {
    const params = new URLSearchParams({
        desde: normalizarFechaLocal(desde),
        hasta: normalizarFechaLocal(hasta),
    });
    return peticionApi(`/agenda/profesionales/${encodeURIComponent(String(profesionalId))}?${params.toString()}`, { method: "GET" });
}
export const obtenerAgendaProfesional = consultarAgendaProfesional;
/**
 * Crea un turno odontológico (`POST /turnos`), normalizando `inicio` a hora local sin zona (`NaiveDatetime`).
 */
export async function crearTurno(entrada) {
    return peticionApi("/turnos", {
        method: "POST",
        body: {
            ...entrada,
            inicio: normalizarFechaLocal(entrada.inicio),
        },
    });
}
export const postTurno = crearTurno;
/**
 * Crea un bloqueo horario sobre un profesional o sillón (`POST /bloqueos`) y devuelve `turnos_afectados`.
 * Normaliza `inicio` y `fin` a hora local sin zona (`NaiveDatetime`).
 */
export async function crearBloqueo(entrada) {
    return peticionApi("/bloqueos", {
        method: "POST",
        body: {
            ...entrada,
            inicio: normalizarFechaLocal(entrada.inicio),
            fin: normalizarFechaLocal(entrada.fin),
        },
    });
}
export const postBloqueo = crearBloqueo;
