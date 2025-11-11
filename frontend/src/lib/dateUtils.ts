/**
 * Utilidades para formatear fechas y horas en hora de Colombia (America/Bogota)
 * y en español
 */

const COLOMBIA_TIMEZONE = 'America/Bogota'
const SPANISH_LOCALE = 'es-CO'

/**
 * Formatea una fecha/hora en hora de Colombia y español
 * @param date - Fecha a formatear (Date o string ISO)
 * @param options - Opciones de formato
 */
export function formatColombiaTime(
  date: Date | string | null | undefined,
  options: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }
): string {
  if (!date) return '--:--:--'
  
  const dateObj = typeof date === 'string' ? new Date(date) : date
  
  if (isNaN(dateObj.getTime())) return '--:--:--'
  
  // Formatear en hora de Colombia
  return new Intl.DateTimeFormat(SPANISH_LOCALE, {
    ...options,
    timeZone: COLOMBIA_TIMEZONE,
  }).format(dateObj)
}

/**
 * Formatea solo la hora en hora de Colombia
 */
export function formatColombiaTimeOnly(date: Date | string | null | undefined): string {
  return formatColombiaTime(date, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

/**
 * Formatea fecha y hora completa en hora de Colombia
 */
export function formatColombiaDateTime(date: Date | string | null | undefined): string {
  return formatColombiaTime(date, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

/**
 * Formatea solo la fecha en español
 */
export function formatColombiaDate(date: Date | string | null | undefined): string {
  return formatColombiaTime(date, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

/**
 * Obtiene la hora actual en formato de Colombia como string
 */
export function getCurrentColombiaTimeString(): string {
  return formatColombiaTimeOnly(new Date())
}

