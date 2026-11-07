/**
 * Contratos HTTP y tipos compartidos del frontend mínimo (C-18, D3, D4, D5).
 * Refleja exactamente los modelos Pydantic expuestos por `app/api/`.
 */

export type RolUsuario = "administracion" | "recepcion" | "odontologo";
export type Rol = RolUsuario;

export type EstadoTurno = "reservado" | "cancelado" | "atendido" | "ausente";

export type AlcanceBloqueo = "profesional" | "sillon";

export type VistaId = "login" | "agenda" | "crear-turno" | "crear-bloqueo";

export interface CredencialesEntrada {
  username: string;
  password: string;
}

export interface TokenSalida {
  access_token: string;
  token_type: "bearer";
}

export interface DetalleError {
  campo: string;
  mensaje: string;
}

export interface ErrorRespuesta {
  codigo: string;
  mensaje: string;
  detalles?: DetalleError[];
}

export interface ErrorInterpretado {
  codigo: string;
  mensaje: string;
  detalles: DetalleError[];
}

export interface PayloadJwt {
  sub: string;
  rol: RolUsuario;
  exp: number;
  iat?: number;
}

export interface ProfesionalSalida {
  id: number;
  nombre: string;
  apellido: string;
  matricula: string | null;
  activo: boolean;
}

export interface SillonSalida {
  id: number;
  nombre: string;
  activo: boolean;
}

export interface PrestacionSalida {
  id: number;
  nombre: string;
  duracion_minutos: number;
  activa: boolean;
}

export interface PacienteSalida {
  id: number;
  nombre: string;
  apellido: string;
  dni: string;
  telefono: string | null;
  obra_social: string | null;
  nro_afiliado: string | null;
}

export interface ItemAgenda {
  tipo: "turno" | "bloqueo";
  id: number;
  inicio: string;
  fin: string;
  paciente_id?: number | null;
  profesional_id?: number | null;
  sillon_id?: number | null;
  prestacion_id?: number | null;
  estado?: EstadoTurno | string | null;
  alcance?: AlcanceBloqueo | string | null;
  recurso_id?: number | null;
  motivo?: string | null;
}

export interface AgendaResponse {
  recurso_tipo: "profesional" | "sillon";
  recurso_id: number;
  desde: string;
  hasta: string;
  items: ItemAgenda[];
  turnos: ItemAgenda[];
  bloqueos: ItemAgenda[];
}

export interface CrearTurnoRequest {
  paciente_id: number;
  profesional_id: number;
  sillon_id: number;
  prestacion_id: number;
  inicio: string;
}

export type TurnoEntrada = CrearTurnoRequest;

export interface TurnoResponse {
  id: number;
  paciente_id: number;
  profesional_id: number;
  sillon_id: number;
  prestacion_id: number;
  inicio: string;
  fin: string;
  estado: EstadoTurno;
}

export type TurnoSalida = TurnoResponse;

export interface BloqueoEntrada {
  alcance: AlcanceBloqueo;
  recurso_id: number;
  inicio: string;
  fin: string;
  motivo: string;
}

export type CrearBloqueoRequest = BloqueoEntrada;

export interface BloqueoSalida {
  id: number;
  alcance: AlcanceBloqueo;
  recurso_id: number;
  inicio: string;
  fin: string;
  motivo: string;
}

export interface BloqueoCreadoSalida extends BloqueoSalida {
  turnos_afectados: TurnoResponse[];
}
