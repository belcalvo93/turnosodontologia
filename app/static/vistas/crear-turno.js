/**
 * Vista de Crear turno (`#crear-turno`, `POST /turnos`, tarea 3.4 de C-18) para `administracion` y `recepcion`.
 * Ofrece solo recursos activos (`RN-REC-03`), envía `inicio` en hora local sin zona (D5), confirma el `201`
 * con el horario `inicio`–`fin` calculado por la API (`RN-TUR-01`, `RN-TUR-14`) y muestra el `mensaje`
 * (y los `detalles`, si vienen) en español ante `409` o `422` (`RN-TUR-03`, `RN-TUR-05`, `RN-GLO-01`).
 */
import { ErrorClienteApi, crearTurno, filtrarActivos, interpretarErrorApi, listarPacientes, listarPrestaciones, listarProfesionales, listarSillones, } from "../api.js";
import { describirIntervalo, fijarValorInicial, llevarALaVista, marcarCargando, mostrarAlerta, nombreProfesional, obtenerElemento, ocultarAlerta, poblarSelector, proximoDiaHabil, quitarElementosEjemplo, valorEntero, } from "./utilidades.js";
const ID_SECCION = "crear-turno";
const ID_ERROR = "crear-turno-error";
const ID_ERROR_MENSAJE = "crear-turno-error-mensaje";
const ID_ERROR_DETALLES = "crear-turno-error-detalles";
const ID_EXITO = "crear-turno-exito";
const ID_EXITO_MENSAJE = "crear-turno-exito-mensaje";
/** Nombre del campo de la API → etiqueta del formulario, para mostrar los `detalles` del `422`. */
const ETIQUETAS_CAMPOS = {
    paciente_id: "Paciente",
    profesional_id: "Profesional",
    sillon_id: "Sillón de atención",
    prestacion_id: "Prestación",
    inicio: "Fecha y hora de inicio",
};
let catalogos = {
    pacientes: new Map(),
    profesionales: new Map(),
    sillones: new Map(),
    prestaciones: new Map(),
};
let inicializada = false;
function ocultarAlertas() {
    ocultarAlerta(ID_ERROR, ID_ERROR_DETALLES);
    ocultarAlerta(ID_EXITO);
}
function mostrarError(error) {
    if (error instanceof ErrorClienteApi) {
        if (error.status === 401) {
            // `api.ts` ya limpió la sesión y `app.ts` volvió al login con el mensaje.
            return;
        }
        mostrarAlerta(ID_ERROR, ID_ERROR_MENSAJE, ID_ERROR_DETALLES, error.mensaje, error.detalles, ETIQUETAS_CAMPOS);
    }
    else {
        mostrarAlerta(ID_ERROR, ID_ERROR_MENSAJE, ID_ERROR_DETALLES, interpretarErrorApi(error).mensaje);
    }
    llevarALaVista(ID_ERROR);
}
function poblarSelectores() {
    const pacientes = [...catalogos.pacientes.values()];
    poblarSelector(obtenerElemento("turno-paciente"), pacientes.map((p) => ({
        valor: String(p.id),
        texto: `${p.nombre} ${p.apellido} — DNI ${p.dni}`,
    })), "No hay pacientes cargados");
    poblarSelector(obtenerElemento("turno-profesional"), filtrarActivos([...catalogos.profesionales.values()]).map((p) => ({
        valor: String(p.id),
        texto: p.matricula ? `${nombreProfesional(p)} — Mat. ${p.matricula}` : nombreProfesional(p),
    })), "No hay profesionales activos");
    poblarSelector(obtenerElemento("turno-sillon"), filtrarActivos([...catalogos.sillones.values()]).map((s) => ({
        valor: String(s.id),
        texto: s.nombre,
    })), "No hay sillones activos");
    poblarSelector(obtenerElemento("turno-prestacion"), filtrarActivos([...catalogos.prestaciones.values()]).map((pr) => ({
        valor: String(pr.id),
        texto: `${pr.nombre} (${pr.duracion_minutos} min)`,
    })), "No hay prestaciones activas");
}
/**
 * Arma el texto de confirmación con los datos que devolvió la API (el `fin` lo calcula el backend).
 */
function describirTurnoCreado(turno) {
    const paciente = catalogos.pacientes.get(turno.paciente_id);
    const profesional = catalogos.profesionales.get(turno.profesional_id);
    const sillon = catalogos.sillones.get(turno.sillon_id);
    const prestacion = catalogos.prestaciones.get(turno.prestacion_id);
    const textoPaciente = paciente !== undefined ? `${paciente.nombre} ${paciente.apellido}` : `Paciente #${turno.paciente_id}`;
    const textoProfesional = profesional !== undefined ? nombreProfesional(profesional) : `Profesional #${turno.profesional_id}`;
    const textoSillon = sillon !== undefined ? sillon.nombre : `Sillón #${turno.sillon_id}`;
    const textoPrestacion = prestacion !== undefined ? prestacion.nombre : `Prestación #${turno.prestacion_id}`;
    return (`Turno #${turno.id}: ${textoPrestacion} para ${textoPaciente} con ${textoProfesional} ` +
        `en ${textoSillon}, ${describirIntervalo(turno.inicio, turno.fin)}.`);
}
function mostrarExito(turno) {
    const contenedor = obtenerElemento(ID_EXITO);
    const badgeEstado = contenedor?.querySelector(".alert-header .badge") ?? null;
    if (badgeEstado !== null) {
        const punto = document.createElement("span");
        punto.className = "badge-dot";
        badgeEstado.replaceChildren(punto, document.createTextNode(turno.estado));
    }
    mostrarAlerta(ID_EXITO, ID_EXITO_MENSAJE, null, describirTurnoCreado(turno));
    llevarALaVista(ID_EXITO);
}
/**
 * Envía el formulario a `POST /turnos`. Ante un error no limpia la selección del usuario.
 */
export async function enviarFormularioCrearTurno() {
    ocultarAlertas();
    const boton = obtenerElemento("btn-crear-turno-submit");
    const inputInicio = obtenerElemento("turno-inicio");
    marcarCargando(boton, true);
    try {
        const turno = await crearTurno({
            paciente_id: valorEntero(obtenerElemento("turno-paciente")),
            profesional_id: valorEntero(obtenerElemento("turno-profesional")),
            sillon_id: valorEntero(obtenerElemento("turno-sillon")),
            prestacion_id: valorEntero(obtenerElemento("turno-prestacion")),
            inicio: inputInicio?.value ?? "",
        });
        mostrarExito(turno);
    }
    catch (error) {
        mostrarError(error);
    }
    finally {
        marcarCargando(boton, false);
    }
}
/**
 * Carga los catálogos reales de la API y llena los selectores solo con recursos activos (`RN-REC-03`).
 * Se llama cada vez que se muestra la vista.
 */
export async function cargarVistaCrearTurno() {
    quitarElementosEjemplo(ID_SECCION);
    ocultarAlertas();
    try {
        const [pacientes, profesionales, sillones, prestaciones] = await Promise.all([
            listarPacientes(),
            listarProfesionales(),
            listarSillones(),
            listarPrestaciones(),
        ]);
        catalogos = {
            pacientes: new Map(pacientes.map((p) => [p.id, p])),
            profesionales: new Map(profesionales.map((p) => [p.id, p])),
            sillones: new Map(sillones.map((s) => [s.id, s])),
            prestaciones: new Map(prestaciones.map((pr) => [pr.id, pr])),
        };
        poblarSelectores();
    }
    catch (error) {
        mostrarError(error);
    }
}
/**
 * Registra los eventos del formulario `#form-crear-turno` (una sola vez) y quita los datos de muestra.
 */
export function inicializarVistaCrearTurno() {
    quitarElementosEjemplo(ID_SECCION);
    ocultarAlertas();
    if (inicializada) {
        return;
    }
    fijarValorInicial(obtenerElemento("turno-inicio"), proximoDiaHabil("09:00"));
    const formulario = obtenerElemento("form-crear-turno");
    if (formulario !== null) {
        formulario.addEventListener("submit", (evento) => {
            evento.preventDefault();
            void enviarFormularioCrearTurno();
        });
        formulario.addEventListener("reset", () => {
            ocultarAlertas();
        });
        inicializada = true;
    }
}
