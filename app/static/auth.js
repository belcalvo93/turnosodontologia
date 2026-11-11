/**
 * Gestión de sesión JWT en `sessionStorage` y visibilidad RBAC (C-18, D3, RN-ACC-01, RN-ACC-02).
 * Reutiliza la decodificación pura de `frontend/src/logica.ts`.
 */
import { decodificarJwt, decodificarPayloadJwt, esRolValido, vistasPermitidasPorRol, } from "./logica.js";
export { decodificarJwt, decodificarPayloadJwt, esRolValido, vistasPermitidasPorRol };
export const CLAVE_TOKEN_SESION = "access_token";
export const CLAVE_USUARIO_SESION = "username";
export const ETIQUETAS_ROL = {
    administracion: "Administración",
    recepcion: "Recepción",
    odontologo: "Odontólogo",
};
function obtenerAlmacenamiento() {
    try {
        if (typeof sessionStorage !== "undefined") {
            return sessionStorage;
        }
    }
    catch {
        // Entornos sin sessionStorage disponible (p. ej. pruebas en Node sin DOM).
    }
    return null;
}
/**
 * Guarda el `access_token` (y opcionalmente el `username`) en `sessionStorage`
 * y devuelve el payload decodificado del JWT (`sub`, `rol`, `exp`).
 */
export function guardarToken(token, username) {
    const storage = obtenerAlmacenamiento();
    if (storage !== null) {
        storage.setItem(CLAVE_TOKEN_SESION, token);
        if (typeof username === "string" && username.trim().length > 0) {
            storage.setItem(CLAVE_USUARIO_SESION, username.trim());
        }
    }
    return decodificarPayloadJwt(token);
}
export const guardarSesion = guardarToken;
/**
 * Obtiene el token crudo almacenado actualmente en `sessionStorage`, o `null` si no hay sesión.
 */
export function obtenerToken() {
    const storage = obtenerAlmacenamiento();
    if (storage === null) {
        return null;
    }
    return storage.getItem(CLAVE_TOKEN_SESION) ?? storage.getItem("token");
}
/**
 * Obtiene el nombre de usuario guardado en `sessionStorage`, si existe.
 */
export function obtenerUsername() {
    const storage = obtenerAlmacenamiento();
    if (storage === null) {
        return null;
    }
    return storage.getItem(CLAVE_USUARIO_SESION);
}
/**
 * Decodifica el JWT actualmente guardado en `sessionStorage` (`sub`, `rol`, `exp`).
 * Devuelve `null` si no hay token o si fue adulterado con un formato inválido.
 */
export function obtenerPayloadSesion() {
    const token = obtenerToken();
    if (token === null) {
        return null;
    }
    return decodificarPayloadJwt(token);
}
/**
 * Devuelve el rol (`"administracion" | "recepcion" | "odontologo"`) del token en `sessionStorage`.
 */
export function obtenerRolActual() {
    return obtenerPayloadSesion()?.rol ?? null;
}
export const obtenerRol = obtenerRolActual;
/**
 * Devuelve la sesión activa completa si el token en `sessionStorage` es decodificable.
 */
export function obtenerSesionActual() {
    const token = obtenerToken();
    if (token === null) {
        return null;
    }
    const payload = decodificarPayloadJwt(token);
    if (payload === null) {
        return null;
    }
    return {
        token,
        sub: payload.sub,
        rol: payload.rol,
        exp: payload.exp,
        iat: payload.iat,
        username: obtenerUsername(),
    };
}
/**
 * Indica si existe un token en `sessionStorage` con estructura válida y no vencido respecto a `ahoraSegundos`.
 */
export function tieneSesionValida(ahoraSegundos = Math.floor(Date.now() / 1000)) {
    const payload = obtenerPayloadSesion();
    if (payload === null) {
        return false;
    }
    return payload.exp > ahoraSegundos;
}
/**
 * Elimina el token y los metadatos de usuario de `sessionStorage` (`RN-ACC-01`, D3).
 */
export function limpiarSesion() {
    const storage = obtenerAlmacenamiento();
    if (storage !== null) {
        storage.removeItem(CLAVE_TOKEN_SESION);
        storage.removeItem("token");
        storage.removeItem(CLAVE_USUARIO_SESION);
        storage.clear();
    }
}
/**
 * Determina si una vista está permitida para el rol indicado (`RN-ACC-02`).
 */
export function puedeVerVista(rol, vista) {
    if (rol === null) {
        return vista === "login";
    }
    return vistasPermitidasPorRol(rol).includes(vista);
}
