/**
 * Utilidades de DOM compartidas por las vistas de Crear turno y Crear bloqueo (C-18, tareas 3.4 y 3.5).
 * Solo manipulan la interfaz: la lógica pura vive en `frontend/src/logica.ts`.
 */

import type { DetalleError, ProfesionalSalida } from "../types.js";

export interface OpcionSelector {
  valor: string;
  texto: string;
}

export function obtenerElemento<T extends HTMLElement>(id: string): T | null {
  if (typeof document === "undefined") {
    return null;
  }
  return document.getElementById(id) as T | null;
}

/**
 * Quita de una sección todo lo marcado con `data-ejemplo`: las opciones y filas de muestra se eliminan
 * y el resto de los textos de muestra se vacían, para que no quede nada simulado visible.
 */
export function quitarElementosEjemplo(seccionId: string): void {
  const seccion = obtenerElemento<HTMLElement>(seccionId);
  if (seccion === null) {
    return;
  }
  for (const elem of seccion.querySelectorAll("option[data-ejemplo], tr[data-ejemplo]")) {
    elem.remove();
  }
  for (const elem of seccion.querySelectorAll<HTMLElement>("[data-ejemplo]")) {
    if (elem instanceof HTMLTextAreaElement || elem instanceof HTMLInputElement) {
      elem.value = "";
      elem.defaultValue = "";
    } else {
      elem.textContent = "";
    }
    elem.removeAttribute("data-ejemplo");
  }
}

/**
 * Convierte `YYYY-MM-DDTHH:MM[:SS]` (hora local de la API) en `DD/MM/AAAA HH:MM`.
 */
export function formatearFechaHora(iso: string): string {
  const partes = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso.trim());
  if (partes === null) {
    return iso;
  }
  const [, anio, mes, dia, hora, minuto] = partes;
  return `${dia}/${mes}/${anio} ${hora}:${minuto}`;
}

/**
 * Describe un intervalo: `el DD/MM/AAAA de HH:MM a HH:MM` si es el mismo día,
 * o `desde el DD/MM/AAAA HH:MM hasta el DD/MM/AAAA HH:MM` si cruza días.
 */
export function describirIntervalo(inicioIso: string, finIso: string): string {
  const inicio = formatearFechaHora(inicioIso);
  const fin = formatearFechaHora(finIso);
  const [fechaInicio, horaInicio] = inicio.split(" ");
  const [fechaFin, horaFin] = fin.split(" ");
  if (fechaInicio === fechaFin && horaInicio !== undefined && horaFin !== undefined) {
    return `el ${fechaInicio} de ${horaInicio} a ${horaFin}`;
  }
  return `desde el ${inicio} hasta el ${fin}`;
}

export function nombreProfesional(profesional: ProfesionalSalida): string {
  return `${profesional.nombre} ${profesional.apellido}`.trim();
}

/**
 * Valor por defecto de los `<input type="datetime-local">`: el próximo día hábil (lunes a viernes)
 * a la hora indicada, en hora local del navegador (`YYYY-MM-DDTHH:MM`).
 */
export function proximoDiaHabil(hora: string, ahora: Date = new Date()): string {
  const fecha = new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate() + 1);
  while (fecha.getDay() === 0 || fecha.getDay() === 6) {
    fecha.setDate(fecha.getDate() + 1);
  }
  const anio = String(fecha.getFullYear());
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  return `${anio}-${mes}-${dia}T${hora}`;
}

/**
 * Fija el valor inicial de un campo de fecha y hora (también el que restaura "Limpiar formulario").
 */
export function fijarValorInicial(input: HTMLInputElement | null, valor: string): void {
  if (input === null) {
    return;
  }
  input.defaultValue = valor;
  input.value = valor;
}

/**
 * Reemplaza las opciones de un `<select>` conservando la opción elegida si sigue disponible.
 * Si no hay opciones, deja una única opción deshabilitada con `textoVacio`.
 */
export function poblarSelector(
  select: HTMLSelectElement | null,
  opciones: readonly OpcionSelector[],
  textoVacio: string
): void {
  if (select === null) {
    return;
  }
  const valorPrevio = select.value;
  select.replaceChildren();

  if (opciones.length === 0) {
    const vacia = document.createElement("option");
    vacia.value = "";
    vacia.textContent = textoVacio;
    vacia.disabled = true;
    vacia.selected = true;
    select.appendChild(vacia);
    return;
  }

  for (const opcion of opciones) {
    const elem = document.createElement("option");
    elem.value = opcion.valor;
    elem.textContent = opcion.texto;
    select.appendChild(elem);
  }
  select.value = opciones.some((o) => o.valor === valorPrevio) ? valorPrevio : opciones[0].valor;
}

/**
 * Convierte el valor de un `<select>` en número. Si está vacío devuelve `NaN`,
 * que `JSON.stringify` envía como `null` para que la API responda `422` con su mensaje.
 */
export function valorEntero(select: HTMLSelectElement | null): number {
  if (select === null || select.value.trim() === "") {
    return Number.NaN;
  }
  return Number(select.value);
}

/**
 * Muestra una alerta con el `mensaje` de la API y, solo si vienen, sus `detalles` por campo (`RN-GLO-01`).
 * `etiquetas` traduce el nombre técnico del campo a la etiqueta del formulario.
 */
export function mostrarAlerta(
  contenedorId: string,
  mensajeId: string,
  detallesId: string | null,
  mensaje: string,
  detalles: readonly DetalleError[] = [],
  etiquetas: Readonly<Record<string, string>> = {}
): void {
  const contenedor = obtenerElemento<HTMLElement>(contenedorId);
  const parrafo = obtenerElemento<HTMLElement>(mensajeId);
  const lista = detallesId === null ? null : obtenerElemento<HTMLUListElement>(detallesId);

  if (parrafo !== null) {
    parrafo.textContent = mensaje;
  }
  if (lista !== null) {
    lista.replaceChildren();
    for (const detalle of detalles) {
      const item = document.createElement("li");
      item.textContent = `${etiquetas[detalle.campo] ?? detalle.campo}: ${detalle.mensaje}`;
      lista.appendChild(item);
    }
    lista.hidden = detalles.length === 0;
  }
  if (contenedor !== null) {
    contenedor.hidden = false;
  }
}

export function ocultarAlerta(contenedorId: string, detallesId: string | null = null): void {
  const contenedor = obtenerElemento<HTMLElement>(contenedorId);
  if (contenedor !== null) {
    contenedor.hidden = true;
  }
  if (detallesId !== null) {
    const lista = obtenerElemento<HTMLUListElement>(detallesId);
    if (lista !== null) {
      lista.replaceChildren();
      lista.hidden = true;
    }
  }
}

/**
 * Activa o desactiva el estado de carga de un botón de envío.
 */
export function marcarCargando(boton: HTMLButtonElement | null, cargando: boolean): void {
  if (boton === null) {
    return;
  }
  boton.disabled = cargando;
  boton.classList.toggle("is-loading", cargando);
}
