/**
 * @file utils.h
 * @brief Fichero de cabecera para el módulo server/utils, con funciones útiles de manejo de recursos
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 01-03-2025
 */

#ifndef _UTILS_H
#define _UTILS_H

#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <semaphore.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#include <logger/logger.h>

#define SEM_MUTEX "/mutex"     // Nombre del semáforo para zonas críticas.
#define SEM_BARRIER "/barrier" // Nombre del semáforo usado para respetar el máximo de hilos.
#define SEM_ACCEPT "/accept"   // Nombre del semáforo para el acceso al socket para aceptar un cliente.

extern int max_threads;    // Variable global que contiene el máximo de hilos en el sistema.
extern int n_threads;      // Variable global que contiene el número de hilos en el sistema.
extern pthread_t *threads; // Tabla que almacena las IDs de los hilos lanzados.
extern sem_t *mutex;       // Puntero al semáforo `SEM_MUTEX`.
extern sem_t *barrier;     // Puntero al semáforo `SEM_BARRIER'.
extern sem_t *s_accept;    // Puntero al semáforo `SEM_ACCEPT`.

/**
 * @brief Función que inicializa recursos usados por el sistema.
 *
 * Reserva la memoria suficiente como para guardar las IDs del máximo de hilos.
 * Abre los semáforos con nombre con el valor inicial adecuado.
 * También añade una función de liberación de los recursos al finalizar con una
 * llamada a `atexit`.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @return 0 si se inicializan los recursos correctamente, -1 en caso de error.
 */
int init_resources(void);

/**
 * @brief Fija el manejador para la máscara `SIGINT` y bloquea el resto de señales.
 *
 * El manejador se encarga de cerrar los hilos que estén activos en el momento de cerrar el servidor,
 * y después finalizar el programa correctamente.
 * La máscara del hilo que llama a esta función (en principio, el hilo principal) se cambia para
 * bloquear todas las señales salvo `SIGINT`.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @return 0 si se realizan los cambios con éxito, -1 si hay algún error.
 */
int configure_signal_handling(void);

/**
 * @brief Cambia la máscara de señales para bloquearlas todas.
 *
 * Se cambia la máscara del hilo que llama a esta función con una llamada a `pthread_sigmask`, bloqueando
 * todas las señales posibles.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @return 0 si se realizan los cambios con éxito, -1 si hay algún error.
 */
int block_all_signals(void);

#endif