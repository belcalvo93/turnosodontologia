/**
 * Lógica pura del frontend sin dependencias del DOM ni de red (C-18, D3, D4, D5, D7).
 * Testeada de forma aislada con `node --test` en `frontend/tests/logica.test.mjs`.
 */
const ROLES_VALIDOS = new Set([
    "administracion",
    "recepcion",
    "odontologo",
]);
const PATRON_FECHA_SIN_SEGUNDOS = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
const ERROR_GENERICO_ESPANOL = {
    codigo: "error_http",
    mensaje: "No se pudo procesar la solicitud.",
    detalles: [],
};
/**
 * Normaliza un valor proveniente de `<input type="datetime-local">` al formato
 * `YYYY-MM-DDTHH:MM:00` en hora local sin zona horaria (`NaiveDatetime`, D5).
 */
export function normalizarFechaLocal(valor) {
    const limpio = valor.trim();
    if (PATRON_FECHA_SIN_SEGUNDOS.test(limpio)) {
        return `${limpio}:00`;
    }
    return limpio;
}
/**
 * Filtra colecciones de recursos conservando solo los activos (`activo === true` o `activa === true`, RN-REC-03).
 */
export function filtrarActivos(items) {
    return items.filter((item) => item.activo === true || item.activa === true);
}
/**
 * Formatea la etiqueta de paciente para el rol `odontologo` sin exponer datos filiatorios (D4, RN-ACC-03).
 */
export function formatearPacienteId(pacienteId) {
    return `Paciente #${pacienteId}`;
}
export const formatearPacienteOdontologo = formatearPacienteId;
/**
 * Indica si un valor corresponde a uno de los tres roles válidos del sistema (`RN-ACC-02`).
 */
export function esRolValido(valor) {
    return typeof valor === "string" && ROLES_VALIDOS.has(valor);
}
/**
 * Extrae `codigo`, `mensaje` y `detalles` por campo desde el cuerpo JSON de error de la API (`RN-GLO-01`).
 */
export function interpretarErrorApi(cuerpo) {
    if (typeof cuerpo !== "object" || cuerpo === null) {
        return { ...ERROR_GENERICO_ESPANOL, detalles: [] };
    }
    const registro = cuerpo;
    const codigo = typeof registro.codigo === "string" && registro.codigo.trim().length > 0
        ? registro.codigo
        : ERROR_GENERICO_ESPANOL.codigo;
    const mensaje = typeof registro.mensaje === "string" && registro.mensaje.trim().length > 0
        ? registro.mensaje
        : ERROR_GENERICO_ESPANOL.mensaje;
    const detalles = [];
    if (Array.isArray(registro.detalles)) {
        for (const item of registro.detalles) {
            if (typeof item === "object" &&
                item !== null &&
                typeof item.campo === "string" &&
                typeof item.mensaje === "string") {
                detalles.push({
                    campo: item.campo,
                    mensaje: item.mensaje,
                });
            }
        }
    }
    return { codigo, mensaje, detalles };
}
/**
 * Decodifica una cadena en Base64URL a texto UTF-8 usando APIs estándar disponibles en navegador y Node.
 */
function decodificarBase64Url(segmento) {
    if (segmento.length === 0 || /[^A-Za-z0-9\-_]/.test(segmento)) {
        return null;
    }
    const base64 = segmento.replace(/-/g, "+").replace(/_/g, "/");
    const resto = base64.length % 4;
    if (resto === 1) {
        return null;
    }
    const conPadding = resto === 0 ? base64 : base64 + "=".repeat(4 - resto);
    try {
        const binario = atob(conPadding);
        const bytes = new Uint8Array(binario.length);
        for (let i = 0; i < binario.length; i += 1) {
            bytes[i] = binario.charCodeAt(i);
        }
        return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    }
    catch {
        return null;
    }
}
/**
 * Decodifica el payload Base64URL de un JWT y valida la presencia de `sub`, `rol` y `exp` (D3).
 * Devuelve `null` si el token está malformado o no contiene los claims requeridos.
 */
export function decodificarPayloadJwt(token) {
    if (typeof token !== "string" || token.trim().length === 0) {
        return null;
    }
    const partes = token.trim().split(".");
    if (partes.length !== 3 || partes[0].length === 0 || partes[1].length === 0 || partes[2].length === 0) {
        return null;
    }
    const jsonTexto = decodificarBase64Url(partes[1]);
    if (jsonTexto === null) {
        return null;
    }
    try {
        const parsed = JSON.parse(jsonTexto);
        if (typeof parsed !== "object" || parsed === null) {
            return null;
        }
        const obj = parsed;
        if (typeof obj.sub !== "string" ||
            obj.sub.trim().length === 0 ||
            !esRolValido(obj.rol) ||
            typeof obj.exp !== "number" ||
            !Number.isFinite(obj.exp)) {
            return null;
        }
        const resultado = {
            sub: obj.sub,
            rol: obj.rol,
            exp: obj.exp,
        };
        if (typeof obj.iat === "number" && Number.isFinite(obj.iat)) {
            resultado.iat = obj.iat;
        }
        return resultado;
    }
    catch {
        return null;
    }
}
export const decodificarJwt = decodificarPayloadJwt;
/**
 * Devuelve las vistas habilitadas en la navegación según el rol del usuario (`RN-ACC-02`, D3).
 */
export function vistasPermitidasPorRol(rol) {
    if (rol === "administracion") {
        return ["agenda", "crear-turno", "crear-bloqueo"];
    }
    if (rol === "recepcion") {
        return ["agenda", "crear-turno"];
    }
    return ["agenda"];
}
