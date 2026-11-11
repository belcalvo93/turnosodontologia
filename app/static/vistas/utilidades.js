/**
 * Utilidades de DOM compartidas por las vistas de Crear turno y Crear bloqueo (C-18, tareas 3.4 y 3.5).
 * Solo manipulan la interfaz: la lógica pura vive en `frontend/src/logica.ts`.
 */
export function obtenerElemento(id) {
    if (typeof document === "undefined") {
        return null;
    }
    return document.getElementById(id);
}
/**
 * Quita de una sección todo lo marcado con `data-ejemplo`: las opciones y filas de muestra se eliminan
 * y el resto de los textos de muestra se vacían, para que no quede nada simulado visible.
 */
export function quitarElementosEjemplo(seccionId) {
    const seccion = obtenerElemento(seccionId);
    if (seccion === null) {
        return;
    }
    for (const elem of seccion.querySelectorAll("option[data-ejemplo], tr[data-ejemplo]")) {
        elem.remove();
    }
    for (const elem of seccion.querySelectorAll("[data-ejemplo]")) {
        if (elem instanceof HTMLTextAreaElement || elem instanceof HTMLInputElement) {
            elem.value = "";
            elem.defaultValue = "";
        }
        else {
            elem.textContent = "";
        }
        elem.removeAttribute("data-ejemplo");
    }
}
/**
 * Convierte `YYYY-MM-DDTHH:MM[:SS]` (hora local de la API) en `DD/MM/AAAA HH:MM`.
 */
export function formatearFechaHora(iso) {
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
export function describirIntervalo(inicioIso, finIso) {
    const inicio = formatearFechaHora(inicioIso);
    const fin = formatearFechaHora(finIso);
    const [fechaInicio, horaInicio] = inicio.split(" ");
    const [fechaFin, horaFin] = fin.split(" ");
    if (fechaInicio === fechaFin && horaInicio !== undefined && horaFin !== undefined) {
        return `el ${fechaInicio} de ${horaInicio} a ${horaFin}`;
    }
    return `desde el ${inicio} hasta el ${fin}`;
}
export function nombreProfesional(profesional) {
    return `${profesional.nombre} ${profesional.apellido}`.trim();
}
/**
 * Valor por defecto de los `<input type="datetime-local">`: el próximo día hábil (lunes a viernes)
 * a la hora indicada, en hora local del navegador (`YYYY-MM-DDTHH:MM`).
 */
export function proximoDiaHabil(hora, ahora = new Date()) {
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
export function fijarValorInicial(input, valor) {
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
export function poblarSelector(select, opciones, textoVacio) {
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
export function valorEntero(select) {
    if (select === null || select.value.trim() === "") {
        return Number.NaN;
    }
    return Number(select.value);
}
/**
 * Muestra una alerta con el `mensaje` de la API y, solo si vienen, sus `detalles` por campo (`RN-GLO-01`).
 * `etiquetas` traduce el nombre técnico del campo a la etiqueta del formulario.
 */
export function mostrarAlerta(contenedorId, mensajeId, detallesId, mensaje, detalles = [], etiquetas = {}) {
    const contenedor = obtenerElemento(contenedorId);
    const parrafo = obtenerElemento(mensajeId);
    const lista = detallesId === null ? null : obtenerElemento(detallesId);
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
export function ocultarAlerta(contenedorId, detallesId = null) {
    const contenedor = obtenerElemento(contenedorId);
    if (contenedor !== null) {
        contenedor.hidden = true;
    }
    if (detallesId !== null) {
        const lista = obtenerElemento(detallesId);
        if (lista !== null) {
            lista.replaceChildren();
            lista.hidden = true;
        }
    }
}
/**
 * Desplaza la página lo justo para que se vea el elemento, por ejemplo una alerta que aparece arriba
 * del formulario cuando el usuario está abajo, en el botón de envío (en celular siempre pasa).
 */
export function llevarALaVista(id) {
    const elem = obtenerElemento(id);
    if (elem === null || elem.hidden || typeof elem.scrollIntoView !== "function") {
        return;
    }
    const sinAnimacion = typeof window !== "undefined" &&
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    elem.scrollIntoView({ behavior: sinAnimacion ? "auto" : "smooth", block: "nearest" });
}
/**
 * Activa o desactiva el estado de carga de un botón de envío.
 */
export function marcarCargando(boton, cargando) {
    if (boton === null) {
        return;
    }
    boton.disabled = cargando;
    boton.classList.toggle("is-loading", cargando);
}
