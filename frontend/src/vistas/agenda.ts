/**
 * Vista de Agenda de un profesional (`#agenda`, `GET /agenda/profesionales/{id}?desde=&hasta=`, tarea 3.3 de C-18).
 * Carga catálogos según rol (`RN-PAC-03`), renderiza turnos `reservado` y bloqueos en orden cronológico,
 * formatea `"Paciente #<id>"` para `odontologo` y muestra el `mensaje` en español ante `403 sin_permiso` (`RN-ACC-03`).
 */

import {
  ErrorClienteApi,
  consultarAgendaProfesional,
  formatearPacienteId,
  interpretarErrorApi,
  listarPacientes,
  listarPrestaciones,
  listarProfesionales,
  listarSillones,
} from "../api.js";
import { obtenerRolActual } from "../auth.js";
import type {
  AgendaResponse,
  ItemAgenda,
  PacienteSalida,
  PrestacionSalida,
  ProfesionalSalida,
  RolUsuario,
  SillonSalida,
} from "../types.js";
import { quitarElementosEjemplo } from "./utilidades.js";

interface CatalogosAgenda {
  profesionales: Map<number, ProfesionalSalida>;
  sillones: Map<number, SillonSalida>;
  prestaciones: Map<number, PrestacionSalida>;
  pacientes: Map<number, PacienteSalida>;
}

function obtenerElemento<T extends HTMLElement>(id: string): T | null {
  if (typeof document === "undefined") {
    return null;
  }
  return document.getElementById(id) as T | null;
}

export function mostrarAlertaAgenda(mensaje: string): void {
  const contenedor = obtenerElemento<HTMLElement>("agenda-alerta");
  const parrafo = obtenerElemento<HTMLElement>("agenda-alerta-mensaje");
  if (parrafo !== null) {
    parrafo.removeAttribute("data-ejemplo");
    parrafo.textContent = mensaje;
  }
  if (contenedor !== null) {
    contenedor.hidden = false;
  }
}

export function ocultarAlertaAgenda(): void {
  const contenedor = obtenerElemento<HTMLElement>("agenda-alerta");
  const parrafo = obtenerElemento<HTMLElement>("agenda-alerta-mensaje");
  if (parrafo !== null) {
    parrafo.removeAttribute("data-ejemplo");
    parrafo.textContent = "";
  }
  if (contenedor !== null) {
    contenedor.hidden = true;
  }
}

function formatearFechaHoraCorta(iso: string): string {
  const coincidencia = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso.trim());
  if (coincidencia === null) {
    return iso;
  }
  const [, anio, mes, dia, hora, minuto] = coincidencia;
  return `${dia}/${mes}/${anio} ${hora}:${minuto}`;
}

function formatearHorarioRango(inicioIso: string, finIso: string): string {
  const ini = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(inicioIso.trim());
  const fin = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(finIso.trim());
  if (ini === null || fin === null) {
    return `${inicioIso} — ${finIso}`;
  }
  const [, anioI, mesI, diaI, horaI, minI] = ini;
  const [, anioF, mesF, diaF, horaF, minF] = fin;
  if (anioI === anioF && mesI === mesF && diaI === diaF) {
    return `${diaI}/${mesI}/${anioI} ${horaI}:${minI} — ${horaF}:${minF}`;
  }
  return `${diaI}/${mesI}/${anioI} ${horaI}:${minI} — ${diaF}/${mesF}/${anioF} ${horaF}:${minF}`;
}

function nombreCompletoProfesional(prof: ProfesionalSalida): string {
  return `${prof.nombre} ${prof.apellido}`.trim();
}

function etiquetaOpcionProfesional(prof: ProfesionalSalida): string {
  const base = nombreCompletoProfesional(prof);
  const sufijoMatricula = prof.matricula ? ` — Mat. ${prof.matricula}` : "";
  const sufijoInactivo = prof.activo ? "" : " (inactivo)";
  return `${base}${sufijoMatricula}${sufijoInactivo}`;
}

function poblarSelectorProfesionales(
  select: HTMLSelectElement,
  profesionales: readonly ProfesionalSalida[]
): void {
  const valorPrevio = select.value;
  select.replaceChildren();

  for (const prof of profesionales) {
    const opcion = document.createElement("option");
    opcion.value = String(prof.id);
    opcion.textContent = etiquetaOpcionProfesional(prof);
    select.appendChild(opcion);
  }

  if (
    valorPrevio &&
    profesionales.some((p) => String(p.id) === valorPrevio)
  ) {
    select.value = valorPrevio;
  } else if (profesionales.length > 0) {
    select.value = String(profesionales[0].id);
  }
}

function actualizarEncabezadoColumnaRecurso(items: readonly ItemAgenda[]): void {
  const tabla = obtenerElemento<HTMLTableElement>("agenda-tabla");
  if (tabla === null) {
    return;
  }
  const cabeceras = tabla.querySelectorAll<HTMLTableCellElement>("thead th");
  const ultimaCabecera = cabeceras.item(cabeceras.length - 1);
  if (ultimaCabecera === null) {
    return;
  }
  const hayBloqueoProfesional = items.some(
    (item) => item.tipo === "bloqueo" && item.alcance === "profesional"
  );
  ultimaCabecera.textContent = hayBloqueoProfesional
    ? "Profesional"
    : "Sillón de atención";
}

function crearCeldaPacienteTurno(
  item: ItemAgenda,
  rol: RolUsuario | null,
  pacientes: ReadonlyMap<number, PacienteSalida>
): HTMLTableCellElement {
  const td = document.createElement("td");
  td.setAttribute("data-label", "Paciente / Detalle");

  const contenedor = document.createElement("div");
  contenedor.className = "patient-cell";

  const pacienteId = item.paciente_id ?? 0;

  if (rol === "odontologo") {
    const fuerte = document.createElement("strong");
    fuerte.textContent = formatearPacienteId(pacienteId);
    contenedor.appendChild(fuerte);
  } else {
    const paciente = pacientes.get(pacienteId);
    const fuerte = document.createElement("strong");
    fuerte.textContent =
      paciente !== undefined
        ? `${paciente.nombre} ${paciente.apellido}`.trim()
        : formatearPacienteId(pacienteId);
    contenedor.appendChild(fuerte);

    if (paciente !== undefined) {
      const spanDni = document.createElement("span");
      spanDni.className = "dni-tag";
      spanDni.textContent = `DNI ${paciente.dni}`;
      contenedor.appendChild(spanDni);
    }
  }

  td.appendChild(contenedor);
  return td;
}

function crearFilaTurno(
  item: ItemAgenda,
  rol: RolUsuario | null,
  catalogos: CatalogosAgenda
): HTMLTableRowElement {
  const tr = document.createElement("tr");

  const tdHorario = document.createElement("td");
  tdHorario.setAttribute("data-label", "Horario");
  tdHorario.className = "cell-mono";
  tdHorario.textContent = formatearHorarioRango(item.inicio, item.fin);

  const tdTipo = document.createElement("td");
  tdTipo.setAttribute("data-label", "Tipo");
  const badgeTipo = document.createElement("span");
  badgeTipo.className = "badge badge-turno";
  badgeTipo.textContent = "Turno";
  tdTipo.appendChild(badgeTipo);

  const tdEstado = document.createElement("td");
  tdEstado.setAttribute("data-label", "Estado");
  const badgeEstado = document.createElement("span");
  badgeEstado.className = "badge badge-reservado";
  const dot = document.createElement("span");
  dot.className = "badge-dot";
  badgeEstado.append(dot, document.createTextNode(item.estado ?? "reservado"));
  tdEstado.appendChild(badgeEstado);

  const tdPaciente = crearCeldaPacienteTurno(item, rol, catalogos.pacientes);

  const tdPrestacion = document.createElement("td");
  tdPrestacion.setAttribute("data-label", "Prestación / Motivo");
  const prestacion =
    item.prestacion_id !== undefined && item.prestacion_id !== null
      ? catalogos.prestaciones.get(item.prestacion_id)
      : undefined;
  tdPrestacion.textContent =
    prestacion !== undefined
      ? `${prestacion.nombre} (${prestacion.duracion_minutos} min)`
      : `Prestación #${item.prestacion_id ?? "-"}`;

  const tdSillon = document.createElement("td");
  tdSillon.setAttribute("data-label", "Sillón de atención");
  const sillon =
    item.sillon_id !== undefined && item.sillon_id !== null
      ? catalogos.sillones.get(item.sillon_id)
      : undefined;
  tdSillon.textContent =
    sillon !== undefined ? sillon.nombre : `Sillón #${item.sillon_id ?? "-"}`;

  tr.append(tdHorario, tdTipo, tdEstado, tdPaciente, tdPrestacion, tdSillon);
  return tr;
}

function crearFilaBloqueo(
  item: ItemAgenda,
  catalogos: CatalogosAgenda
): HTMLTableRowElement {
  const tr = document.createElement("tr");
  tr.className = "row-bloqueo";

  const esProfesional = item.alcance === "profesional";

  const tdHorario = document.createElement("td");
  tdHorario.setAttribute("data-label", "Horario");
  tdHorario.className = "cell-mono";
  tdHorario.textContent = formatearHorarioRango(item.inicio, item.fin);

  const tdTipo = document.createElement("td");
  tdTipo.setAttribute("data-label", "Tipo");
  const badgeTipo = document.createElement("span");
  badgeTipo.className = "badge badge-bloqueo";
  badgeTipo.textContent = "Bloqueo";
  tdTipo.appendChild(badgeTipo);

  const tdEstado = document.createElement("td");
  tdEstado.setAttribute("data-label", "Estado");
  const badgeEstado = document.createElement("span");
  badgeEstado.className = "badge badge-warning";
  const dot = document.createElement("span");
  dot.className = "badge-dot";
  badgeEstado.append(dot, document.createTextNode("bloqueado"));
  tdEstado.appendChild(badgeEstado);

  const tdDetalle = document.createElement("td");
  tdDetalle.setAttribute("data-label", "Paciente / Detalle");
  const contenedorDetalle = document.createElement("div");
  contenedorDetalle.className = "patient-cell";
  const fuerte = document.createElement("strong");
  fuerte.textContent = "Horario no disponible";
  const etiquetaAlcance = document.createElement("span");
  etiquetaAlcance.className = "dni-tag";
  etiquetaAlcance.textContent = esProfesional ? "Profesional" : "Sillón de atención";
  contenedorDetalle.append(fuerte, etiquetaAlcance);
  tdDetalle.appendChild(contenedorDetalle);

  const tdMotivo = document.createElement("td");
  tdMotivo.setAttribute("data-label", "Prestación / Motivo");
  tdMotivo.textContent =
    item.motivo && item.motivo.trim().length > 0
      ? item.motivo
      : "Bloqueo horario";

  const tdRecurso = document.createElement("td");
  tdRecurso.setAttribute(
    "data-label",
    esProfesional ? "Profesional" : "Sillón de atención"
  );
  const recursoId = item.recurso_id ?? 0;
  if (esProfesional) {
    const prof = catalogos.profesionales.get(recursoId);
    tdRecurso.textContent =
      prof !== undefined ? nombreCompletoProfesional(prof) : `Profesional #${recursoId}`;
  } else {
    const sillon = catalogos.sillones.get(recursoId);
    tdRecurso.textContent =
      sillon !== undefined ? sillon.nombre : `Sillón #${recursoId}`;
  }

  tr.append(tdHorario, tdTipo, tdEstado, tdDetalle, tdMotivo, tdRecurso);
  return tr;
}

function renderizarResultadoAgenda(
  agenda: AgendaResponse,
  rol: RolUsuario | null,
  catalogos: CatalogosAgenda
): void {
  const tbody = obtenerElemento<HTMLTableSectionElement>("agenda-tbody");
  const contenedorTabla = obtenerElemento<HTMLElement>("agenda-tabla-contenedor");
  const estadoVacio = obtenerElemento<HTMLElement>("agenda-vacia");
  const resumenRango = obtenerElemento<HTMLElement>("agenda-resumen-rango");
  const contadorItems = obtenerElemento<HTMLElement>("agenda-contador-items");

  const itemsOrdenados = [...agenda.items]
    .filter((item) => item.tipo === "bloqueo" || item.estado === "reservado" || item.estado === undefined || item.estado === null)
    .sort((a, b) => a.inicio.localeCompare(b.inicio) || a.id - b.id);

  const prof = catalogos.profesionales.get(agenda.recurso_id);
  const nombreProf =
    prof !== undefined
      ? nombreCompletoProfesional(prof)
      : `Profesional #${agenda.recurso_id}`;

  if (resumenRango !== null) {
    resumenRango.removeAttribute("data-ejemplo");
    resumenRango.textContent = `${nombreProf} — ${formatearFechaHoraCorta(agenda.desde)} a ${formatearFechaHoraCorta(agenda.hasta)}`;
  }

  if (contadorItems !== null) {
    contadorItems.removeAttribute("data-ejemplo");
    const total = itemsOrdenados.length;
    contadorItems.textContent =
      total === 1 ? "1 horario en agenda" : `${total} horarios en agenda`;
  }

  actualizarEncabezadoColumnaRecurso(itemsOrdenados);

  if (tbody !== null) {
    tbody.replaceChildren();
    for (const item of itemsOrdenados) {
      const fila =
        item.tipo === "bloqueo"
          ? crearFilaBloqueo(item, catalogos)
          : crearFilaTurno(item, rol, catalogos);
      tbody.appendChild(fila);
    }
  }

  const sinItems = itemsOrdenados.length === 0;
  if (contenedorTabla !== null) {
    contenedorTabla.hidden = sinItems;
  }
  if (estadoVacio !== null) {
    estadoVacio.hidden = !sinItems;
  }
}

function limpiarTablaAnteError(): void {
  const tbody = obtenerElemento<HTMLTableSectionElement>("agenda-tbody");
  const contenedorTabla = obtenerElemento<HTMLElement>("agenda-tabla-contenedor");
  const estadoVacio = obtenerElemento<HTMLElement>("agenda-vacia");
  const contadorItems = obtenerElemento<HTMLElement>("agenda-contador-items");

  if (tbody !== null) {
    tbody.replaceChildren();
  }
  if (contenedorTabla !== null) {
    contenedorTabla.hidden = true;
  }
  if (estadoVacio !== null) {
    estadoVacio.hidden = true;
  }
  if (contadorItems !== null) {
    contadorItems.textContent = "0 horarios en agenda";
  }
}

async function cargarCatalogosSegunRol(rol: RolUsuario | null): Promise<CatalogosAgenda> {
  const promesasBase = Promise.all([
    listarProfesionales(),
    listarSillones(),
    listarPrestaciones(),
  ]);
  const promesaPacientes: Promise<PacienteSalida[]> =
    rol === "administracion" || rol === "recepcion"
      ? listarPacientes()
      : Promise.resolve([]);

  const [[profesionales, sillones, prestaciones], pacientes] = await Promise.all([
    promesasBase,
    promesaPacientes,
  ]);

  return {
    profesionales: new Map(profesionales.map((p) => [p.id, p])),
    sillones: new Map(sillones.map((s) => [s.id, s])),
    prestaciones: new Map(prestaciones.map((pr) => [pr.id, pr])),
    pacientes: new Map(pacientes.map((pa) => [pa.id, pa])),
  };
}

let catalogosActuales: CatalogosAgenda = {
  profesionales: new Map(),
  sillones: new Map(),
  prestaciones: new Map(),
  pacientes: new Map(),
};

let listenerRegistrado = false;

/**
 * Ejecuta la consulta de agenda con los valores actuales del formulario `#form-agenda`.
 */
export async function ejecutarConsultaAgenda(): Promise<void> {
  ocultarAlertaAgenda();

  const selectProf = obtenerElemento<HTMLSelectElement>("agenda-profesional");
  const inputDesde = obtenerElemento<HTMLInputElement>("agenda-desde");
  const inputHasta = obtenerElemento<HTMLInputElement>("agenda-hasta");
  const botonConsultar = obtenerElemento<HTMLButtonElement>("btn-consultar-agenda");

  if (selectProf === null || inputDesde === null || inputHasta === null) {
    return;
  }

  const profesionalId = Number(selectProf.value);
  const desde = inputDesde.value;
  const hasta = inputHasta.value;

  if (!Number.isFinite(profesionalId) || profesionalId <= 0) {
    return;
  }

  if (botonConsultar !== null) {
    botonConsultar.disabled = true;
    botonConsultar.classList.add("is-loading");
  }

  try {
    const rol = obtenerRolActual();
    const respuesta = await consultarAgendaProfesional(profesionalId, desde, hasta);
    renderizarResultadoAgenda(respuesta, rol, catalogosActuales);
  } catch (error: unknown) {
    limpiarTablaAnteError();
    if (error instanceof ErrorClienteApi) {
      mostrarAlertaAgenda(error.mensaje);
    } else {
      mostrarAlertaAgenda(interpretarErrorApi(error).mensaje);
    }
  } finally {
    if (botonConsultar !== null) {
      botonConsultar.disabled = false;
      botonConsultar.classList.remove("is-loading");
    }
  }
}

/**
 * Carga los catálogos reales de la API (sin llamar a `GET /pacientes` cuando el rol es `odontologo`),
 * elimina los nodos `data-ejemplo` y ejecuta la consulta inicial de la agenda.
 */
export async function cargarVistaAgenda(): Promise<void> {
  quitarElementosEjemplo("agenda");
  ocultarAlertaAgenda();

  const rol = obtenerRolActual();
  const selectProf = obtenerElemento<HTMLSelectElement>("agenda-profesional");

  try {
    catalogosActuales = await cargarCatalogosSegunRol(rol);
    if (selectProf !== null) {
      poblarSelectorProfesionales(
        selectProf,
        Array.from(catalogosActuales.profesionales.values())
      );
    }
    await ejecutarConsultaAgenda();
  } catch (error: unknown) {
    limpiarTablaAnteError();
    if (error instanceof ErrorClienteApi) {
      mostrarAlertaAgenda(error.mensaje);
    } else {
      mostrarAlertaAgenda(interpretarErrorApi(error).mensaje);
    }
  }
}

/**
 * Registra los eventos de la vista de Agenda (`#form-agenda`) y limpia los elementos `data-ejemplo`.
 */
export function inicializarVistaAgenda(): void {
  quitarElementosEjemplo("agenda");
  ocultarAlertaAgenda();

  if (listenerRegistrado) {
    return;
  }

  const formulario = obtenerElemento<HTMLFormElement>("form-agenda");
  const selectProf = obtenerElemento<HTMLSelectElement>("agenda-profesional");

  if (formulario !== null) {
    formulario.addEventListener("submit", async (evento: SubmitEvent) => {
      evento.preventDefault();
      await ejecutarConsultaAgenda();
    });
    listenerRegistrado = true;
  }

  if (selectProf !== null) {
    selectProf.addEventListener("change", () => {
      ocultarAlertaAgenda();
    });
  }
}

export const montarVistaAgenda = inicializarVistaAgenda;
export const initAgenda = inicializarVistaAgenda;
export const refrescarAgenda = cargarVistaAgenda;
