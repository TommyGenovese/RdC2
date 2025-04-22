/**
 * @file utils.c
 * @brief Fichero de implementación del módulo server/utils, con funciones útiles de manejo de recursos
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 01-03-2025
 */

#include "server/utils.h"

int max_threads = 0;          // Variable global que contiene el máximo de hilos en el sistema.
int n_threads = 0;            // Variable global que contiene el número de hilos en el sistema.
pthread_t *threads = NULL;    // Tabla que almacena las IDs de los hilos lanzados.
sem_t *mutex = SEM_FAILED;    // Puntero al semáforo `SEM_MUTEX`.
sem_t *barrier = SEM_FAILED;  // Puntero al semáforo `SEM_BARRIER'.
sem_t *s_accept = SEM_FAILED; // Puntero al semáforo `SEM_ACCEPT`.

/**
 * @brief Manejador de la señal `SIGINT`.
 *
 * Cancela los hilos que estén activos en el momento de lanzar la interrupción
 * y luego termina la ejecución.
 *
 * @param sig La señal recibida (en principio, `SIGINT`).
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
static void sigint_handler(__attribute__((unused)) int sig) {
    int i;

    // El hilo principal cancela todos los hilos que tengan identificador en la tabla.
    // Protegido por semáforo para evitar cancelar un hilo que está cerrando sus recursos.
    sem_wait(mutex);
    for (i = 0; i < n_threads; i++) {
        pthread_cancel(threads[i]);
    }
    sem_post(mutex);

    // Espera unos segundos a que los hilos cancelados terminen.
    // Esto evita errores de valgrind.
    sleep(2);

    log_info("Server closed.");
    pthread_exit(NULL);
}

/**
 * @brief Función de liberación de los recursos.
 *
 * Está en el formato requerido por la función `atexit`
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
static void cleanup_resources(void) {
    free(threads);
    sem_close(mutex);
    sem_unlink(SEM_MUTEX);
    sem_close(barrier);
    sem_unlink(SEM_BARRIER);
    sem_close(s_accept);
    sem_unlink(SEM_ACCEPT);
}

/**
 * @brief Crea un semáforo con nombre con un valor inicial dado
 *
 * En concreto, abre un semáforo con banderas `O_CREAT` y `O_EXCL`,
 * para garantizar que el semáforo se crea con el valor inicial adecuado.
 * En caso de fallo verifica si se debe a la existencia previa
 * del semáforo, lo elimina e intenta volver a crear el semáforo.
 *
 * @param name Nombre del semáforo
 * @param value El valor inicial que se dará al semáforo
 *
 * @return El puntero al semáforo, o `SEM_FAILED` si hay algún error.
 */
static sem_t *new_named_sem(const char *name, int value) {
    sem_t *sem = SEM_FAILED;

    // Primer intento de creación del semáforo
    sem = sem_open(name, O_CREAT | O_EXCL,
                   S_IRUSR | S_IRGRP | S_IROTH | S_IWUSR | S_IWGRP | S_IWOTH, value);

    // En caso de error
    if (SEM_FAILED == sem) {
        // Se comprueba si el error es por existencia previa del semáforo
        if (EEXIST == errno) {
            log_warning("Semaphore already existed. Destroying the semaphore and creating a new one.");
            sem_unlink(name); // Se elimina el semáforo
            // Se abre otra vez
            sem = sem_open(name, O_CREAT | O_EXCL,
                           S_IRUSR | S_IRGRP | S_IROTH | S_IWUSR | S_IWGRP | S_IWOTH, value);

            // Si vuelve a fallar, se retorna SEM_FAILED
            if (SEM_FAILED == sem) {
                log_error(strerror(errno));
                return SEM_FAILED;
            }
        } else {
            // Si es otro tipo de error, se retorna SEM_FAILED
            log_error(strerror(errno));
            return SEM_FAILED;
        }
    }
    return sem;
}

int init_resources(void) {

    if (max_threads <= 0) {
        log_error("Maximum number of clients must be greater than 0.");
        return -1;
    }

    // Reserva la memoria para la tabla de hilos
    threads = malloc(max_threads * sizeof(pthread_t));
    if (NULL == threads) {
        log_error(strerror(errno));
        return -1;
    }

    // Creación del semáforo SEM_MUTEX
    mutex = new_named_sem(SEM_MUTEX, 1);
    if (SEM_FAILED == mutex) {
        free(threads);
        return -1;
    }

    // Creación del semáforo SEM_BARRIER
    barrier = new_named_sem(SEM_BARRIER, max_threads);
    if (SEM_FAILED == barrier) {
        free(threads);
        sem_close(mutex);
        sem_unlink(SEM_MUTEX);
        return -1;
    }

    // Creación del semáforo SEM_ACCEPT
    s_accept = new_named_sem(SEM_ACCEPT, 1);
    if (SEM_FAILED == s_accept) {
        free(threads);
        sem_close(mutex);
        sem_unlink(SEM_MUTEX);
        sem_close(barrier);
        sem_unlink(SEM_BARRIER);
        return -1;
    }

    // Fija la función de liberación de recursos para que se llame al salir con atexit
    if (0 != atexit(cleanup_resources)) {
        log_error("Unable to push cleanup function for system resources.");
        free(threads);
        sem_close(mutex);
        sem_unlink(SEM_MUTEX);
        sem_close(barrier);
        sem_unlink(SEM_BARRIER);
        sem_close(s_accept);
        sem_unlink(SEM_ACCEPT);
        return -1;
    }

    log_info("Resources initialised successfully.");
    return 0;
}

int configure_signal_handling(void) {
    sigset_t mask;
    struct sigaction sigint_action;

    // Bloquea las señales excepto SIGINT
    if (-1 == sigfillset(&mask)) {
        log_error(strerror(errno));
        return -1;
    }
    if (-1 == sigdelset(&mask, SIGINT)) {
        log_error(strerror(errno));
        return -1;
    }
    if (0 != pthread_sigmask(SIG_SETMASK, &mask, NULL)) {
        log_error(strerror(errno));
        return -1;
    }

    // Fija el manejador de SIGINT
    sigint_action.sa_flags = 0;
    sigint_action.sa_handler = sigint_handler;
    if (-1 == sigfillset(&(sigint_action.sa_mask))) {
        log_error(strerror(errno));
        return -1;
    }

    if (-1 == sigaction(SIGINT, &sigint_action, NULL)) {
        log_error(strerror(errno));
        return -1;
    }

    log_info("Interruption handler configured successfully.");
    return 0;
}

int block_all_signals(void) {
    sigset_t mask;

    if (-1 == sigfillset(&mask)) {
        log_error(strerror(errno));
        return -1;
    }
    if (0 != pthread_sigmask(SIG_SETMASK, &mask, NULL)) {
        log_error(strerror(errno));
        return -1;
    }

    return 0;
}