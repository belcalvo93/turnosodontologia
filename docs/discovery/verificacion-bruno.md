# Verificación de fuente — Bruno Fiouchetta

- **Tipo de fuente:** sitio oficial
- **Fuente:** https://agendapro.com/ar/dental/software-odontologico
- **Fuente adicional revisada:** https://agendapro.com/ar/planes (enlace "Precios" del menú de la misma página)
- **Fecha de verificación:** 2026-10-09
- **Cómo se verificó:** abrí la página en el navegador, sin crear cuenta ni iniciar sesión. Además del texto visible, revisé las respuestas colapsadas de las preguntas frecuentes y seguí el enlace "Precios" del menú.

## Resultado: Parcial (2 afirmaciones incorrectas)

| Afirmación del informe | ¿Está en la URL? | Observación |
|---|---|---|
| Reserva online sin registro del paciente | Sí | Textual: "Reserva online sin necesidad de que el paciente se registre". |
| Recordatorios por WhatsApp, SMS o email con doble confirmación | Sí | Textual. Agrega un dato que el informe no tiene: el envío se configura para el mismo día o 1, 2 o 3 días antes del turno. |
| Liberación automática ante cancelaciones | Sí | Textual: "Liberá espacios de agenda automáticamente ante una cancelación". |
| Sin precios publicados | **No** | La landing dental no los muestra, pero el enlace "Precios" lleva a https://agendapro.com/ar/planes, con precios en pesos e IVA incluido: Individual $13.900/mes (1 profesional), Básico $33.900, Premium $44.900, Pro $314.900. Hay cobro mensual o anual (anual con 2 meses gratis) y una promoción de los 3 primeros meses a $990. El informe había probado `/ar/precios`, que da 404, y concluyó mal que no había precios. |
| No menciona odontograma | **No** | Lo menciona en la respuesta colapsada de una pregunta frecuente ("herramientas especializadas como el odontograma") y en la descripción de la página ("odontograma digital"). No aparece en el texto visible sin desplegar. |

## Corrección propuesta (Ajustar)

1. **A.10 Modelo comercial, AgendaPro:**
   - "Precios publicados": de "No evidenciado (agendapro.com/ar/precios devolvió 404)" a "Comprobado: Individual $13.900, Básico $33.900, Premium $44.900, Pro $314.900 ARS/mes IVA incluido (https://agendapro.com/ar/planes)".
   - "Moneda": ARS.
   - "Modalidad de cobro": "Mensual o anual (anual con 2 meses gratis)".
   - "Costos adicionales": "WhatsApp desde $7.900/mes por 50 mensajes; videoconferencia desde $10.900/mes; asistente Charly desde $31.900/mes (Comprobado)".
2. **A.5 Gestión odontológica, AgendaPro:** "Odontograma" de "No evidenciado" a "Declarado (respuesta de preguntas frecuentes y descripción de la página)".
3. **A.3 Turnos digitales, AgendaPro:** "Canales" de "No evidenciado como canal de reserva" a "Declarado (link de reserva para compartir en redes sociales; turnos online 24/7)".
4. **A.4 Automatización, AgendaPro:** agregar "envío configurable el mismo día o 1, 2 o 3 días antes".
5. **A.6 / A.7, AgendaPro:** "Facturación electrónica" figura como "Próximamente" en la página de planes: queda "No evidenciado".
6. **B. Matriz:** revisar el puntaje de AgendaPro en "Precio y facilidad de adopción": con precios publicados y promoción, sube de 2 a 4 o 5.
7. **Resumen ejecutivo y C.3:** la afirmación "solo Turnito publica precios en pesos" deja de ser cierta. AgendaPro también los publica, y además es un producto con versión dental.

## Observaciones

- **Dos errores del informe vienen del método del agente:**
  - Probó una URL de precios inventada (`/ar/precios`) en lugar de seguir el enlace real del menú.
  - El resumen automático de la página no incluyó el contenido de las preguntas frecuentes colapsadas.

  Las dos afirmaciones parecían razonables y estaban mal. Es un hallazgo para la reflexión.
- La página de planes también lista "Facturación electrónica: Próximamente", e "Integraciones / API: No" en la comparación de planes.
- La página muestra testimonios de rubros de belleza y bienestar (masajistas, barberos, estilistas), no de odontólogos, lo que refuerza que es un producto horizontal.
