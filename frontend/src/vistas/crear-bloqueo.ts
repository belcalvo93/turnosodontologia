/**
 * Vista de Crear bloqueo (`#crear-bloqueo`, `POST /bloqueos`, tarea 3.5 de C-18), exclusiva de `administracion`.
 * Selector de `alcance` (`profesional` o `sillon`) con selector dinámico de `recurso_id`, campos `inicio`,
 * `fin` y `motivo` (`RN-REC-02`). Muestra el `mensaje` en español de la API ante `422` (por ejemplo,
 * `inicio >= fin`) y, ante `201`, la tabla informativa de `turnos_afectados` o el aviso de lista vacía
 * (`RN-TUR-04`, `RN-TUR-05`, `RN-TUR-08`). La tabla no ofrece acciones (D6).
 */

import {
  ErrorClienteApi,
  crearBloqueo,
  filtrarActivos,
  formatearPacienteId,
  interpretarErrorApi,
  listarPacientes,
  listarPrestaciones,
  listarProfesionales,
  listarSillones,
} from "../api.js";
import type {
  AlcanceBloqueo,
  BloqueoCreadoSalida,
  PacienteSalida,
  PrestacionSalida,
  ProfesionalSalida,
  SillonSalida,
  TurnoResponse,
} from "../types.js";
import {
  describirIntervalo,
  fijarValorInicial,
  formatearFechaHora,
  marcarCargando,
  mostrarAlerta,
  nombreProfesional,
  obtenerElemento,
  ocultarAlerta,
  poblarSelector,
  proximoDiaHabil,
  quitarElementosEjemplo,
  valorEntero,
} from "./utilidades.js";

const ID_SECCION = "crear-bloqueo";
const ID_ERROR = "crear-bloqueo-error";
const ID_ERROR_MENSAJE = "crear-bloqueo-error-mensaje";
const ID_ERROR_DETALLES = "crear-bloqueo-error-detalles";
const ID_EXITO = "crear-bloqueo-exito";
const ID_EXITO_MENSAJE = "crear-bloqueo-exito-mensaje";
const ID_PANEL_AFECTADOS = "panel-turnos-afectados";

const ETIQUETA_ALCANCE: Readonly<Record<AlcanceBloqueo, string>> = {
  profesional: "Profesional",
  sillon: "Sillón de atención",
};

const AYUDA_RECURSO: Readonly<Record<AlcanceBloqueo, string>> = {
  profesional: "Profesional cuya agenda se suspenderá.",
  sillon: "Sillón de atención que no estará disponible.",
};

/** Nombre del campo de la API → etiqueta del formulario, para mostrar los `detalles` del `422`. */
const ETIQUETAS_CAMPOS: Readonly<Record<string, string>> = {
  alcance: "Aplicar bloqueo sobre",
  recurso_id: "Profesional o sillón de atención",
  inicio: "Fecha y hora de inicio",
  fin: "Fecha y hora de fin",
  motivo: "Motivo del bloqueo",
};

interface CatalogosBloqueo {
  profesionales: Map<number, ProfesionalSalida>;
  sillones: Map<number, SillonSalida>;
  pacientes: Map<number, PacienteSalida>;
  prestaciones: Map<number, PrestacionSalida>;
}

let catalogos: CatalogosBloqueo = {
  profesionales: new Map(),
  sillones: new Map(),
  pacientes: new Map(),
  prestaciones: new Map(),
};

let inicializada = false;

function alcanceSeleccionado(): AlcanceBloqueo {
  const select = obtenerElemento<HTMLSelectElement>("bloqueo-alcance");
  return select?.value === "sillon" ? "sillon" : "profesional";
}

function ocultarPanelAfectados(): void {
  const panel = obtenerElemento<HTMLElement>(ID_PANEL_AFECTADOS);
  if (panel !== null) {
    panel.hidden = true;
  }
}

function ocultarResultados(): void {
  ocultarAlerta(ID_ERROR, ID_ERROR_DETALLES);
  ocultarAlerta(ID_EXITO);
  ocultarPanelAfectados();
}

function mostrarError(error: unknown): void {
  if (error instanceof ErrorClienteApi) {
    if (error.status === 401) {
      // `api.ts` ya limpió la sesión y `app.ts` volvió al login con el mensaje.
      return;
    }
    mostrarAlerta(ID_ERROR, ID_ERROR_MENSAJE, ID_ERROR_DETALLES, error.mensaje, error.detalles, ETIQUETAS_CAMPOS);
    return;
  }
  mostrarAlerta(ID_ERROR, ID_ERROR_MENSAJE, ID_ERROR_DETALLES, interpretarErrorApi(error).mensaje);
}

function nombreRecurso(alcance: AlcanceBloqueo, recursoId: number): string {
  if (alcance === "profesional") {
    const profesional = catalogos.profesionales.get(recursoId);
    return profesional !== undefined ? nombreProfesional(profesional) : `Profesional #${recursoId}`;
  }
  const sillon = catalogos.sillones.get(recursoId);
  return sillon !== undefined ? sillon.nombre : `Sillón #${recursoId}`;
}

/**
 * Llena el selector de recurso según el alcance elegido y ajusta su etiqueta y su ayuda.
 */
function actualizarSelectorRecurso(): void {
  const alcance = alcanceSeleccionado();
  const select = obtenerElemento<HTMLSelectElement>("bloqueo-recurso");

  const etiqueta = document.querySelector<HTMLElement>('label[for="bloqueo-recurso"] > span');
  const textoEtiqueta = etiqueta?.firstChild ?? null;
  if (textoEtiqueta !== null && textoEtiqueta.nodeType === Node.TEXT_NODE) {
    textoEtiqueta.textContent = `${ETIQUETA_ALCANCE[alcance]} `;
  }
  const ayuda = select?.parentElement?.querySelector<HTMLElement>(".field-help") ?? null;
  if (ayuda !== null) {
    ayuda.textContent = AYUDA_RECURSO[alcance];
  }

  if (alcance === "profesional") {
    poblarSelector(
      select,
      filtrarActivos([...catalogos.profesionales.values()]).map((p) => ({
        valor: String(p.id),
        texto: p.matricula ? `${nombreProfesional(p)} — Mat. ${p.matricula}` : nombreProfesional(p),
      })),
      "No hay profesionales activos"
    );
  } else {
    poblarSelector(
      select,
      filtrarActivos([...catalogos.sillones.values()]).map((s) => ({
        valor: String(s.id),
        texto: s.nombre,
      })),
      "No hay sillones activos"
    );
  }
}

function crearCelda(etiqueta: string, contenido: string | Node, clase?: string): HTMLTableCellElement {
  const td = document.createElement("td");
  td.setAttribute("data-label", etiqueta);
  if (clase !== undefined) {
    td.className = clase;
  }
  if (typeof contenido === "string") {
    td.textContent = contenido;
  } else {
    td.appendChild(contenido);
  }
  return td;
}

function crearBloqueDosLineas(clase: string, principal: string, secundaria: string, claseSecundaria: string): HTMLElement {
  const contenedor = document.createElement("div");
  contenedor.className = clase;
  const fuerte = document.createElement(clase === "patient-cell" ? "strong" : "span");
  fuerte.textContent = principal;
  contenedor.appendChild(fuerte);
  if (secundaria.length > 0) {
    const sub = document.createElement("span");
    sub.className = claseSecundaria;
    sub.textContent = secundaria;
    contenedor.appendChild(sub);
  }
  return contenedor;
}

/**
 * Fila informativa de un turno afectado: sin acciones de cancelar, reprogramar, notificar ni exportar (D6).
 */
function crearFilaTurnoAfectado(turno: TurnoResponse, alcance: AlcanceBloqueo, etiquetaRecurso: string): HTMLTableRowElement {
  const fila = document.createElement("tr");

  const paciente = catalogos.pacientes.get(turno.paciente_id);
  const celdaPaciente =
    paciente !== undefined
      ? crearBloqueDosLineas("patient-cell", `${paciente.nombre} ${paciente.apellido}`, `DNI ${paciente.dni}`, "dni-tag")
      : crearBloqueDosLineas("patient-cell", formatearPacienteId(turno.paciente_id), "", "dni-tag");

  const prestacion = catalogos.prestaciones.get(turno.prestacion_id);
  const textoPrestacion = prestacion !== undefined ? prestacion.nombre : `Prestación #${turno.prestacion_id}`;
  const textoProfesional = nombreRecurso("profesional", turno.profesional_id);
  const textoSillon = nombreRecurso("sillon", turno.sillon_id);

  // El recurso bloqueado va primero; el otro recurso y la prestación quedan como dato secundario.
  const celdaRecurso =
    alcance === "profesional"
      ? crearBloqueDosLineas("resource-cell", textoProfesional, `${textoSillon} · ${textoPrestacion}`, "sub-tag")
      : crearBloqueDosLineas("resource-cell", textoSillon, `${textoProfesional} · ${textoPrestacion}`, "sub-tag");

  const badgeEstado = document.createElement("span");
  badgeEstado.className = "badge badge-reservado";
  const punto = document.createElement("span");
  punto.className = "badge-dot";
  badgeEstado.append(punto, document.createTextNode(turno.estado));

  fila.append(
    crearCelda("Turno", `#${turno.id}`, "cell-mono"),
    crearCelda("Paciente", celdaPaciente),
    crearCelda(etiquetaRecurso, celdaRecurso),
    crearCelda("Inicio", formatearFechaHora(turno.inicio), "cell-mono"),
    crearCelda("Fin", formatearFechaHora(turno.fin), "cell-mono"),
    crearCelda("Estado", badgeEstado)
  );
  return fila;
}

/**
 * Renderiza la tabla de `turnos_afectados` o el aviso de lista vacía.
 */
function renderizarTurnosAfectados(bloqueo: BloqueoCreadoSalida): void {
  const panel = obtenerElemento<HTMLElement>(ID_PANEL_AFECTADOS);
  const contador = obtenerElemento<HTMLElement>("turnos-afectados-contador");
  const contenedorTabla = obtenerElemento<HTMLElement>("turnos-afectados-tabla-contenedor");
  const tbody = obtenerElemento<HTMLTableSectionElement>("turnos-afectados-tbody");
  const vacio = obtenerElemento<HTMLElement>("turnos-afectados-vacio");
  const tabla = obtenerElemento<HTMLTableElement>("tabla-turnos-afectados");

  const afectados = [...bloqueo.turnos_afectados].sort(
    (a, b) => a.inicio.localeCompare(b.inicio) || a.id - b.id
  );
  const etiquetaRecurso = ETIQUETA_ALCANCE[bloqueo.alcance];

  // La columna del recurso se llama como el recurso bloqueado: "Profesional" o "Sillón de atención".
  const cabeceraRecurso = tabla?.querySelectorAll<HTMLTableCellElement>("thead th").item(2) ?? null;
  if (cabeceraRecurso !== null) {
    cabeceraRecurso.textContent = etiquetaRecurso;
  }

  if (tbody !== null) {
    tbody.replaceChildren(...afectados.map((t) => crearFilaTurnoAfectado(t, bloqueo.alcance, etiquetaRecurso)));
  }
  if (contador !== null) {
    contador.textContent = afectados.length === 1 ? "1 turno afectado" : `${afectados.length} turnos afectados`;
  }

  const sinAfectados = afectados.length === 0;
  if (contenedorTabla !== null) {
    contenedorTabla.hidden = sinAfectados;
  }
  if (vacio !== null) {
    vacio.hidden = !sinAfectados;
  }
  if (panel !== null) {
    panel.hidden = false;
  }
}

function mostrarExito(bloqueo: BloqueoCreadoSalida): void {
  const badgeAlcance = obtenerElemento<HTMLElement>("crear-bloqueo-exito-alcance");
  if (badgeAlcance !== null) {
    badgeAlcance.textContent = ETIQUETA_ALCANCE[bloqueo.alcance];
  }
  const motivo = bloqueo.motivo.trim().length > 0 ? ` Motivo: ${bloqueo.motivo}.` : "";
  mostrarAlerta(
    ID_EXITO,
    ID_EXITO_MENSAJE,
    null,
    `Bloqueo #${bloqueo.id} de ${nombreRecurso(bloqueo.alcance, bloqueo.recurso_id)} ` +
      `${describirIntervalo(bloqueo.inicio, bloqueo.fin)}.${motivo}`
  );
  renderizarTurnosAfectados(bloqueo);
}

/**
 * Envía el formulario a `POST /bloqueos`. El intervalo lo valida la API (`422` si `inicio >= fin`).
 */
export async function enviarFormularioCrearBloqueo(): Promise<void> {
  ocultarResultados();
  const boton = obtenerElemento<HTMLButtonElement>("btn-crear-bloqueo-submit");

  marcarCargando(boton, true);
  try {
    const bloqueo = await crearBloqueo({
      alcance: alcanceSeleccionado(),
      recurso_id: valorEntero(obtenerElemento<HTMLSelectElement>("bloqueo-recurso")),
      inicio: obtenerElemento<HTMLInputElement>("bloqueo-inicio")?.value ?? "",
      fin: obtenerElemento<HTMLInputElement>("bloqueo-fin")?.value ?? "",
      motivo: obtenerElemento<HTMLTextAreaElement>("bloqueo-motivo")?.value ?? "",
    });
    mostrarExito(bloqueo);
  } catch (error: unknown) {
    mostrarError(error);
  } finally {
    marcarCargando(boton, false);
  }
}

/**
 * Carga profesionales y sillones para el selector de recurso, y pacientes y prestaciones para
 * describir los turnos afectados. Se llama cada vez que se muestra la vista.
 */
export async function cargarVistaCrearBloqueo(): Promise<void> {
  quitarElementosEjemplo(ID_SECCION);
  ocultarResultados();

  try {
    const [profesionales, sillones, pacientes, prestaciones] = await Promise.all([
      listarProfesionales(),
      listarSillones(),
      listarPacientes(),
      listarPrestaciones(),
    ]);
    catalogos = {
      profesionales: new Map(profesionales.map((p) => [p.id, p])),
      sillones: new Map(sillones.map((s) => [s.id, s])),
      pacientes: new Map(pacientes.map((p) => [p.id, p])),
      prestaciones: new Map(prestaciones.map((pr) => [pr.id, pr])),
    };
    actualizarSelectorRecurso();
  } catch (error: unknown) {
    mostrarError(error);
  }
}

/**
 * Registra los eventos del formulario `#form-crear-bloqueo` (una sola vez) y quita los datos de muestra.
 */
export function inicializarVistaCrearBloqueo(): void {
  quitarElementosEjemplo(ID_SECCION);
  ocultarResultados();

  if (inicializada) {
    return;
  }

  fijarValorInicial(obtenerElemento<HTMLInputElement>("bloqueo-inicio"), proximoDiaHabil("09:00"));
  fijarValorInicial(obtenerElemento<HTMLInputElement>("bloqueo-fin"), proximoDiaHabil("13:00"));

  const selectAlcance = obtenerElemento<HTMLSelectElement>("bloqueo-alcance");
  if (selectAlcance !== null) {
    selectAlcance.addEventListener("change", () => {
      actualizarSelectorRecurso();
    });
  }

  const formulario = obtenerElemento<HTMLFormElement>("form-crear-bloqueo");
  if (formulario !== null) {
    formulario.addEventListener("submit", (evento: SubmitEvent) => {
      evento.preventDefault();
      void enviarFormularioCrearBloqueo();
    });
    formulario.addEventListener("reset", () => {
      ocultarResultados();
      // El navegador restablece los campos después del evento `reset`.
      setTimeout(() => {
        actualizarSelectorRecurso();
      }, 0);
    });
    inicializada = true;
  }
}
