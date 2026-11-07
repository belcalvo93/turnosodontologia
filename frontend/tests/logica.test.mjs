import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  ErrorClienteApi,
  iniciarSesion,
  peticionApi,
  registrarManejadorNoAutenticado,
} from "../../app/static/api.js";
import {
  guardarToken,
  limpiarSesion,
  obtenerRolActual,
  obtenerSesionActual,
  obtenerToken,
  puedeVerVista,
} from "../../app/static/auth.js";
import {
  decodificarPayloadJwt,
  filtrarActivos,
  formatearPacienteId,
  interpretarErrorApi,
  normalizarFechaLocal,
} from "../../app/static/logica.js";

/**
 * Genera un token JWT de prueba con el payload indicado en Base64URL.
 * @param {unknown} payload
 * @returns {string}
 */
function crearJwtPrueba(payload) {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${header}.${body}.firma_ficticia`;
}

/**
 * Crea un doble de `sessionStorage` en memoria para pruebas en Node.
 */
function instalarSessionStorageEnMemoria() {
  const mapa = new Map();
  globalThis.sessionStorage = {
    get length() {
      return mapa.size;
    },
    clear() {
      mapa.clear();
    },
    getItem(key) {
      return mapa.has(key) ? mapa.get(key) : null;
    },
    key(index) {
      return Array.from(mapa.keys())[index] ?? null;
    },
    removeItem(key) {
      mapa.delete(key);
    },
    setItem(key, value) {
      mapa.set(String(key), String(value));
    },
  };
  return mapa;
}

describe("normalizarFechaLocal (D5, NaiveDatetime)", () => {
  it("agrega ':00' cuando el valor datetime-local viene sin segundos (YYYY-MM-DDTHH:MM)", () => {
    assert.equal(normalizarFechaLocal("2026-11-05T09:30"), "2026-11-05T09:30:00");
    assert.equal(normalizarFechaLocal(" 2026-12-01T18:05 "), "2026-12-01T18:05:00");
  });

  it("conserva los segundos cuando el valor ya tiene formato YYYY-MM-DDTHH:MM:SS", () => {
    assert.equal(normalizarFechaLocal("2026-11-05T09:30:00"), "2026-11-05T09:30:00");
    assert.equal(normalizarFechaLocal("2026-11-05T14:15:45"), "2026-11-05T14:15:45");
  });
});

describe("filtrarActivos (RN-REC-03)", () => {
  it("filtra profesionales y sillones conservando únicamente los que tienen activo === true", () => {
    const recursos = [
      { id: 1, nombre: "Sillón 1", activo: true },
      { id: 2, nombre: "Sillón 2 (mantenimiento)", activo: false },
      { id: 3, nombre: "Sillón 3", activo: true },
    ];
    const activos = filtrarActivos(recursos);
    assert.deepEqual(
      activos.map((r) => r.id),
      [1, 3]
    );
  });

  it("filtra prestaciones conservando únicamente las que tienen activa === true", () => {
    const prestaciones = [
      { id: 10, nombre: "Consulta ficticia", duracion_minutos: 30, activa: true },
      { id: 11, nombre: "Práctica dada de baja", duracion_minutos: 60, activa: false },
    ];
    const activas = filtrarActivos(prestaciones);
    assert.equal(activas.length, 1);
    assert.equal(activas[0].id, 10);
  });
});

describe("formatearPacienteId (D4, RN-ACC-03)", () => {
  it("formatea el identificador numérico con el prefijo exacto 'Paciente #<id>'", () => {
    assert.equal(formatearPacienteId(1), "Paciente #1");
    assert.equal(formatearPacienteId(42), "Paciente #42");
  });

  it("funciona con distintos identificadores positivos sin agregar datos personales", () => {
    const texto = formatearPacienteId(105);
    assert.equal(texto, "Paciente #105");
    assert.ok(!texto.includes("DNI"));
  });
});

describe("interpretarErrorApi (D5, RN-GLO-01)", () => {
  it("extrae codigo y mensaje en español cuando la respuesta de error no trae detalles", () => {
    const cuerpo = {
      codigo: "conflicto_agenda",
      mensaje: "El profesional ya tiene un turno asignado en ese horario.",
    };
    const resultado = interpretarErrorApi(cuerpo);
    assert.equal(resultado.codigo, "conflicto_agenda");
    assert.equal(resultado.mensaje, "El profesional ya tiene un turno asignado en ese horario.");
    assert.deepEqual(resultado.detalles, []);
  });

  it("extrae la lista de detalles por campo cuando un error 422 los incluye", () => {
    const cuerpo = {
      codigo: "dato_invalido",
      mensaje: "Los datos enviados no son válidos.",
      detalles: [
        { campo: "inicio", mensaje: "Valor inválido." },
        { campo: "motivo", mensaje: "No puede estar vacío." },
      ],
    };
    const resultado = interpretarErrorApi(cuerpo);
    assert.equal(resultado.codigo, "dato_invalido");
    assert.equal(resultado.mensaje, "Los datos enviados no son válidos.");
    assert.equal(resultado.detalles.length, 2);
    assert.deepEqual(resultado.detalles[0], { campo: "inicio", mensaje: "Valor inválido." });
  });

  it("devuelve un mensaje genérico en español si el cuerpo no tiene el formato esperado", () => {
    const resultado = interpretarErrorApi(null);
    assert.equal(resultado.codigo, "error_http");
    assert.equal(resultado.mensaje, "No se pudo procesar la solicitud.");
    assert.deepEqual(resultado.detalles, []);
  });
});

describe("decodificarPayloadJwt (D3, RN-ACC-01, RN-ACC-02)", () => {
  it("decodifica sub, rol y exp de un JWT válido para cada rol del sistema", () => {
    const tokenAdmin = crearJwtPrueba({
      sub: "1",
      rol: "administracion",
      iat: 1762340000,
      exp: 1762341800,
    });
    const payload = decodificarPayloadJwt(tokenAdmin);
    assert.deepEqual(payload, {
      sub: "1",
      rol: "administracion",
      iat: 1762340000,
      exp: 1762341800,
    });

    const tokenOdontologo = crearJwtPrueba({
      sub: "3",
      rol: "odontologo",
      exp: 1762350000,
    });
    const payloadOdontologo = decodificarPayloadJwt(tokenOdontologo);
    assert.equal(payloadOdontologo?.rol, "odontologo");
    assert.equal(payloadOdontologo?.exp, 1762350000);
    assert.equal(payloadOdontologo?.sub, "3");
  });

  it("devuelve null ante un token vacío, con formato inválido o con claims faltantes/inválidos", () => {
    assert.equal(decodificarPayloadJwt(""), null);
    assert.equal(decodificarPayloadJwt("token-sin-segmentos"), null);
    assert.equal(decodificarPayloadJwt("a.@@@.c"), null);

    const tokenRolInvalido = crearJwtPrueba({
      sub: "1",
      rol: "superusuario_inexistente",
      exp: 1762341800,
    });
    assert.equal(decodificarPayloadJwt(tokenRolInvalido), null);

    const tokenSinExp = crearJwtPrueba({
      sub: "1",
      rol: "recepcion",
    });
    assert.equal(decodificarPayloadJwt(tokenSinExp), null);
  });
});

describe("auth en sessionStorage y RBAC (tarea 3.1, RN-ACC-01, RN-ACC-02)", () => {
  it("guarda el token en sessionStorage, expone el rol y verifica vistas permitidas", () => {
    instalarSessionStorageEnMemoria();
    const token = crearJwtPrueba({
      sub: "2",
      rol: "recepcion",
      exp: 9999999999,
    });
    const payload = guardarToken(token, "recepcion_demo");
    assert.equal(payload?.rol, "recepcion");
    assert.equal(obtenerToken(), token);
    assert.equal(obtenerRolActual(), "recepcion");
    assert.equal(obtenerSesionActual()?.username, "recepcion_demo");
    assert.equal(puedeVerVista("recepcion", "agenda"), true);
    assert.equal(puedeVerVista("recepcion", "crear-turno"), true);
    assert.equal(puedeVerVista("recepcion", "crear-bloqueo"), false);

    limpiarSesion();
    assert.equal(obtenerToken(), null);
    assert.equal(obtenerRolActual(), null);
  });
});

describe("cliente fetch API (tarea 3.1, RN-ACC-01, RN-GLO-01)", () => {
  it("adjunta Authorization Bearer cuando hay token en sessionStorage", async () => {
    instalarSessionStorageEnMemoria();
    const token = crearJwtPrueba({
      sub: "1",
      rol: "administracion",
      exp: 9999999999,
    });
    guardarToken(token);

    let cabeceraAuthRecibida = null;
    const fetchOriginal = globalThis.fetch;
    globalThis.fetch = async (_url, init) => {
      const headers = new Headers(init?.headers);
      cabeceraAuthRecibida = headers.get("Authorization");
      return new Response(JSON.stringify([{ id: 1, nombre: "Sillón 1", activo: true }]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    try {
      const datos = await peticionApi("/sillones");
      assert.equal(cabeceraAuthRecibida, `Bearer ${token}`);
      assert.equal(Array.isArray(datos), true);
    } finally {
      globalThis.fetch = fetchOriginal;
      limpiarSesion();
    }
  });

  it("limpia sessionStorage e invoca el manejador ante 401 no_autenticado", async () => {
    instalarSessionStorageEnMemoria();
    sessionStorage.setItem("access_token", "token-adulterado");

    let errorNotificado = null;
    registrarManejadorNoAutenticado((err) => {
      errorNotificado = err;
    });

    const fetchOriginal = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          codigo: "no_autenticado",
          mensaje: "Se requiere un token de acceso válido.",
        }),
        {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }
      );

    try {
      await assert.rejects(
        () => peticionApi("/profesionales"),
        (err) => {
          assert.ok(err instanceof ErrorClienteApi);
          assert.equal(err.status, 401);
          assert.equal(err.codigo, "no_autenticado");
          assert.equal(err.mensaje, "Se requiere un token de acceso válido.");
          return true;
        }
      );
      assert.equal(obtenerToken(), null);
      assert.equal(errorNotificado?.codigo, "no_autenticado");
    } finally {
      globalThis.fetch = fetchOriginal;
      registrarManejadorNoAutenticado(null);
    }
  });

  it("propaga 401 credenciales_invalidas en login sin invocar el manejador de sesión vencida", async () => {
    instalarSessionStorageEnMemoria();
    let llamadoNoAutenticado = false;
    registrarManejadorNoAutenticado(() => {
      llamadoNoAutenticado = true;
    });

    const fetchOriginal = globalThis.fetch;
    globalThis.fetch = async () =>
      new Response(
        JSON.stringify({
          codigo: "credenciales_invalidas",
          mensaje: "Usuario o contraseña incorrectos.",
        }),
        {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }
      );

    try {
      await assert.rejects(
        () => iniciarSesion({ username: "admin_demo", password: "err" }),
        (err) => {
          assert.ok(err instanceof ErrorClienteApi);
          assert.equal(err.status, 401);
          assert.equal(err.codigo, "credenciales_invalidas");
          assert.equal(err.mensaje, "Usuario o contraseña incorrectos.");
          return true;
        }
      );
      assert.equal(llamadoNoAutenticado, false);
    } finally {
      globalThis.fetch = fetchOriginal;
      registrarManejadorNoAutenticado(null);
    }
  });
});
