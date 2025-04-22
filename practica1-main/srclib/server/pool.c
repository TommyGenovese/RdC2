/**
 * @file pool.c
 * @brief Fichero de implementación del módulo server/pool, usado para la implementación de un servidor
 * con pool de hilos
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 04-03-2025
 */

#include "server/pool.h"

static pool_args_t args = {.socket_fd = -1, .process = NULL};

/**
 * @brief Función que cierra el descriptor de la conexión con el cliente,
 * en el formato requerido por `pthread_cleanup_push`.
 *
 * @param args Puntero al descriptor de la conexión
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
static void pool_cleanup_fd(void *args) {
    int connection_fd;
    connection_fd = *(int *)args;
    close(connection_fd);
    log_info("Connection closed.");
}

/**
 * @brief Función usada de "start routine" al lanzar el hilo.
 *
 * @param args Puntero a una estructura de tipo `pool_args_t` con el descriptor de
 * la conexión y la función de procesamiento de peticiones.
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 */
static void *pool_process(void *args) {
    p_process_func process;
    int socket_fd, connection_fd;

    process = ((pool_args_t *)args)->process;
    socket_fd = ((pool_args_t *)args)->socket_fd;
    if (-1 == block_all_signals()) {
        log_error("Unable to block signals.");
        pthread_exit(NULL);
    }

    while (1) {
        sem_wait(s_accept);
        connection_fd = get_client_from_socket(socket_fd);
        sem_post(s_accept);
        if (-1 == connection_fd) {
            log_warning("Failed connection.");
            continue;
        }
        pthread_cleanup_push(pool_cleanup_fd, (void *)&connection_fd);
        process(connection_fd);
        pthread_cleanup_pop(1);
    }
}

int pool_dispatch_threads(p_process_func process, int socket_fd) {
    int i, j, ret;

    args.process = process;
    args.socket_fd = socket_fd;

    for (i = 0; i < max_threads; i++) {
        if (0 != (ret = pthread_create(threads + i, NULL, pool_process, (void *)&args))) {
            log_error(strerror(ret));
            for (j = 0; j < i; j++) {
                pthread_cancel(threads[j]);
            }
            return -1;
        }
        if (0 != (ret = pthread_detach(threads[i]))) {
            log_error(strerror(ret));
            for (j = 0; j < i; j++) {
                pthread_cancel(threads[j]);
            }
            pthread_cancel(threads[i]);
            pthread_join(threads[i], NULL);
            return -1;
        }
    }

    log_info("Thread pool created successfully.");
    return 0;
}

void pool_main_suspend(void) {
    sigset_t mask;

    configure_signal_handling();
    pthread_sigmask(0, NULL, &mask);
    log_info("Server ready to accept clients.");
    sigsuspend(&mask);
}