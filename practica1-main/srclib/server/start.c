/**
 * @file start.c
 * @brief Fichero de implementación del módulo server/start, con funciones para abrir un socket y aceptar una conexión
 *
 * @authors Ignacio Seisdedos, Tommaso Genovese
 * @date 01-03-2025
 */

#include "server/start.h"

int socket_fd = -1; // Variable global para el descriptor del socket del servidor

void cleanup_socket_fd(void) {
    close(socket_fd);
}

int get_server_socket(int port) {
    int fd;
    struct sockaddr_in server_address;
    char errstr[30] = "";
    uint16_t uport;

    uport = (uint16_t)port;
    if (port < 0 || port > 0xFFFF) {
        log_warning("Port number exceeds 16-bit limits.");
        sprintf(errstr, "Casted to 16-bit: %u.", uport);
        log_warning(errstr);
    }
    if (0 == port) {
        log_error("Invalid port number.");
        return -1;
    }

    // Apertura del socket
    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (-1 == fd) {
        log_error(strerror(errno));
        return -1;
    }

    if (-1 == setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &(int){1}, sizeof(int))) {
        log_warning(strerror(errno));
    }

    server_address.sin_family = AF_INET;
    server_address.sin_addr.s_addr = htonl(INADDR_ANY);
    server_address.sin_port = htons(uport);

    // Binding del socket
    if (-1 == bind(fd, (const struct sockaddr *)&server_address, sizeof(server_address))) {
        log_error(strerror(errno));
        close(fd);
        return -1;
    }

    // Escucha en el socket con una cola de hasta `SOMAXCONN` clientes.
    if (-1 == listen(fd, SOMAXCONN)) {
        log_error(strerror(errno));
        close(fd);
        return -1;
    }

    log_info("Socket opened successfully.");
    return fd;
}

int get_client_from_socket(int socket_fd) {
    int connection_fd, addr_len;
    struct sockaddr_in client_address;
    struct timeval timeout = {.tv_sec = 30, .tv_usec = 0};

    // Acepta un cliente
    addr_len = sizeof(client_address);
    connection_fd = accept(socket_fd, (struct sockaddr *)&client_address, (socklen_t *)&addr_len);
    if (-1 == connection_fd) {
        log_warning(strerror(errno));
        close(socket_fd);
        return -1;
    }

    if (-1 == setsockopt(connection_fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout))) {
        log_warning(strerror(errno));
    }

    log_info("Accepted new connection.");
    return connection_fd;
}

void ping(int connection_fd) {
    char buffer[BUFF_SIZE];
    while (1) {
        bzero(buffer, BUFF_SIZE);
        // Lee del socket
        // Si el cliente se ha desconectado, sale de la función
        if (0 >= read(connection_fd, buffer, BUFF_SIZE)) {
            break;
        }
        // Escribe el mensaje leído en el socket
        write(connection_fd, buffer, BUFF_SIZE);
    }
}