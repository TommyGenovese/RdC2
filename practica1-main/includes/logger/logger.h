/**
 * @file logger.h
 * @brief Fichero de cabecera para el módulo logger, que se encarga del fichero de loggeo
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 11-03-2025
 */

#ifndef _LOGGER_H
#define _LOGGER_H

#include <fcntl.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <time.h>
#include <unistd.h>

#define ERROR "ERROR"     // Cadena usada para indicar mensaje de error
#define INFO "INFO"       // Cadena usada para indicar mensaje de información
#define WARNING "WARNING" // Cadena usada para indicar mensaje de warning

/**
 * @brief Escribe en el logger
 *
 * `mode` puede ser una de las cadenas predefinidas: `ERROR`, `INFO` o `WARNING`;
 * o una introducida por el usuario; indica el tipo de mensaje que se está escribiendo.
 * El formato del mensaje será "[fecha y hora] `mode`: `msg`".
 *
 * @param mode El tipo de mensaje que se quiere escribir.
 * @param msg El mensaje a escribir.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se escribe con éxito, -1 si hay algún error.
 */
int logger_write(const char *mode, const char *msg);

/**
 * @brief Inicializa los recursos del logger.
 *
 * @param logfile_name El nombre del fichero de loggeo.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se inicializa el logger correctamente, -1 si hay algún error.
 */
int logger_start(const char *logfile_name);

/**
 * @brief Loggea un mensaje de error.
 *
 * Esta función llama internamente a `logger_write` con el valor de `ERROR`
 * para `mode`.
 *
 * @param mesg El mensaje a escribir.
 * 
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se escribe con éxito, -1 si hay algún error.
 */
int log_error(const char *msg);

/**
 * @brief Loggea un mensaje de información.
 *
 * Esta función llama internamente a `logger_write` con el valor de `INFO`
 * para `mode`.
 *
 * @param mesg El mensaje a escribir.
 * 
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se escribe con éxito, -1 si hay algún error.
 */
int log_info(const char *msg);

/**
 * @brief Loggea un mensaje de warning.
 *
 * Esta función llama internamente a `logger_write` con el valor de `WARNING`
 * para `mode`.
 *
 * @param mesg El mensaje a escribir.
 * 
 * @authors Ignacio Seisdedos, Tommaso Genovese
 *
 * @return 0 si se escribe con éxito, -1 si hay algún error.
 */
int log_warning(const char *msg);

/**
 * @brief Función de liberación de los recursos del logger.
 * 
 * En el formato requerido por la función `atexit`.
 * 
 * @authors Ignacio Seisdedos, Tommaso Genovese
*/
void logger_end(void);

#endif