#include "server.h"
#include "logger/logger.h"
#include "config/config.h"
#include "http/http_response.h"

#define MAX_THREADS 20

int main() {
    int port, connection_fd;
    server_mode_t mode = ITERATIVE;

    if (-1 == config_start()) {
        fprintf(stderr, "Unable to read configuration file.\n");
        exit(EXIT_FAILURE);
    }
    port = config.listen_port;
    mode = config.server_mode;
    max_threads = config.max_clients;

    if (-1 == logger_start(config.logger_path)) {
        exit(EXIT_FAILURE);
    }

    if (-1 == block_all_signals()) {
        log_error("Unable to block signals.");
        exit(EXIT_FAILURE);
    }
    log_info("Signals blocked successfully.");

    if (-1 == init_resources()) {
        log_error("Failed to initialise resources.");
        exit(EXIT_FAILURE);
    }

    if (ITERATIVE == mode && max_threads > 1) {
        log_warning("Server configured as iterative (single threaded), max_clients ignored.");
    }

    socket_fd = get_server_socket(port);
    if (-1 == socket_fd) {
        log_error("Unable to open socket.");
        exit(EXIT_FAILURE);
    }
    atexit(cleanup_socket_fd);

    switch (mode) {
    case POOL:
        n_threads = max_threads;
        if (-1 == pool_dispatch_threads(handle_http_request, socket_fd)) {
            log_error("Failed to dispatch threads.");
            exit(EXIT_FAILURE);
        }
        pool_main_suspend();
        break;
    case REACTIVE:
        if (-1 == configure_signal_handling()) {
            log_error("Configuration of interruption handling failed.");
            exit(EXIT_FAILURE);
        }
        log_info("Server ready to accept clients.");
        while (1) {
            sem_wait(barrier);
            connection_fd = get_client_from_socket(socket_fd);
            if (-1 == connection_fd) {
                sem_post(barrier);
                log_warning("Failed connection.");
                continue;
            }
            react_dispatch_thread(handle_http_request, connection_fd);
        }
        break;
    default:
        if (-1 == configure_signal_handling()) {
            log_error("Configuration of interruption handling failed.");
            exit(EXIT_FAILURE);
        }
        log_info("Server ready to accept clients.");
        while (1) {
            connection_fd = get_client_from_socket(socket_fd);
            if (-1 == connection_fd) {
                log_warning("Failed connection.");
                continue;
            }
            handle_http_request(connection_fd);
            close(connection_fd);
            log_info("Connection closed.");
        }
        break;
    }
}