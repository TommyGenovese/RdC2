#include "http/http_response.h"
#include "config/config.h"
#include "http/cgi.h"

#define MAX_URI_SIZE 2048

/**
 * @brief Lista de códigos de estado soportados por el servidor.
 */
static http_status_t status_codes[] = {
    {200, "OK"},
    //{301, "Moved Permanently"},
    //{302, "Temporary Redirect"},
    {400, "Bad Request"},
    //{401, "Unauthorized"},
    //{403, "Forbidden"},
    {404, "Not Found"},
    {500, "Internal Server Error"},
    {501, "Not Implemented"},
    {0, NULL} // terminador
};

/**
 * @brief Obtiene el mensaje asociado a un código de estado HTTP.
 *
 * @param status_code Código de estado HTTP.
 * @return Mensaje correspondiente al código de estado o "Unknown status code" si no se encuentra.
 */
const char *get_status_message(int status_code) {
    for (int i = 0; status_codes[i].code != 0; i++) {
        if (status_codes[i].code == status_code) {
            return status_codes[i].message;
        }
    }
    return "Unknown status code";
}

/**
 * @brief Obtiene la ruta completa a partir de la ruta recibida por el socket.
 *
 * @param client_fd Descriptor de archivo de la conexión del cliente.
 * @param full_path Cadena en la que se guardará la ruta completa, de al menos 4096 caracteres.
 * @param path La ruta recibida.
 *
 * @return 0 si se obtiene una ruta correcta, -1 en caso de error o si la ruta recibida no es
 * válida.
 */
int get_full_path(int client_fd, char *full_path, const char *path) {
    if (config.server_root == NULL) {
        send_http_response(client_fd, 500, "text/html", "<h1>500 Internal Server Error</h1>");
        return -1;
    }

    if (strcmp(path, "/") == 0) {
        // log_info("Serving index.html");
        path = "index.html"; //  "/", servimo index.html
    }

    if (strstr(path, "..")) {
        send_http_response(client_fd, 400, "text/html", "<h1>400 Bad Request</h1>");
        return -1;
    }

    // Costruye la ruta completa del recurso solicitado
    if (snprintf(full_path, MAX_FULL_PATH, "%s%s", config.server_root, path) >= MAX_FULL_PATH) {
        send_http_response(client_fd, 400, "text/html", "<h1>400 Bad Request: Path too long</h1>");
        return -1;
    }

    return 0;
}

/**
 * @brief Envía una respuesta HTTP al cliente.
 *
 * @param connection_fd Descriptor de archivo de la conexión del cliente.
 * @param status_code Código de estado HTTP de la respuesta.
 * @param content_type Tipo de contenido de la respuesta.
 * @param body Cuerpo del mensaje HTTP.
 * @return Número de bytes escritos en el socket.
 */
int send_http_response(int connection_fd, int status_code, const char *content_type, const char *body) {
    char *response = NULL, header_line[BUFF_SIZE];
    int content_length = strlen(body), response_length, bytes_written = 0, write_ret;

    // Genera la cabecera de la respuesta y anade el cuerpo
    snprintf(header_line, BUFF_SIZE - 1,
             "HTTP/1.1 %d %s\r\n", // status_code
             status_code, get_status_message(status_code));
    response = stradd(response, header_line);
    snprintf(header_line, BUFF_SIZE - 1,
             "Content-Type: %s\r\n", // content_type
             content_type);
    response = stradd(response, header_line);
    snprintf(header_line, BUFF_SIZE - 1,
             "Content-Length: %d\r\n", // content_length
             content_length);
    response = stradd(response, header_line);
    response = stradd(response, "Connection: close\r\n");
    response = stradd(response, "\r\n");
    response = stradd(response, body);

    if (NULL == response) {
        log_error("Could not build dynamic string.");
        return -1;
    }

    response_length = strlen(response);
    while (bytes_written < response_length) {
        write_ret = write(connection_fd, response + bytes_written, response_length - bytes_written);
        if (write_ret < 0) {
            if (EPIPE == errno) {
                log_warning("Client closed the connection before receiving a response.");
            } else {
                log_error(strerror(errno));
            }
            break;
        }
        bytes_written += write_ret;
    }
    free(response);
    return bytes_written;
}

/**
 * @brief Maneja una solicitud HTTP GET y envía el recurso solicitado si existe.
 *
 * @param client_fd Descriptor de archivo del cliente.
 * @param path Ruta del recurso solicitado.
 */
void handle_GET_request(int client_fd, const char *path) {
    struct stat file_stat;

    char full_path[MAX_FULL_PATH];

    if (-1 == get_full_path(client_fd, full_path, path)) {
        log_info("Requested path wasn't valid.");
        return;
    }

    char **argv = parse_script_args(full_path);
    pthread_cleanup_push(args_free, (void *)argv);

    if (stat(full_path, &file_stat) < 0) {
        send_http_response(client_fd, 404, "text/html", "<h1>404 Not Found</h1>");
        goto clean_argv;
    }

    if (NULL == argv) {
        int file_fd = open(full_path, O_RDONLY);
        if (file_fd < 0) { // Si no abre el fichero
            send_http_response(client_fd, 500, "text/html", "<h1>500 Internal Server Error</h1>");
            goto clean_argv;
        }

        char header[512];
        char date[64];
        char last_modified[64];

        time_t now = time(NULL);
        struct tm tm;
        gmtime_r(&now, &tm);
        strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", &tm);

        gmtime_r(&file_stat.st_mtime, &tm);
        strftime(last_modified, sizeof(last_modified), "%a, %d %b %Y %H:%M:%S GMT", &tm);

        // determinar el tipo de contenuto
        const char *content_type = "text/plain"; // Default
        if (strstr(full_path, ".html") || strstr(full_path, ".htm")) {
            content_type = "text/html";
        } else if (strstr(full_path, ".gif")) {
            content_type = "image/gif";
        } else if (strstr(full_path, ".jpeg") || strstr(full_path, ".jpg")) {
            content_type = "image/jpeg";
        } else if (strstr(full_path, ".mpeg") || strstr(full_path, ".mpg")) {
            content_type = "video/mpeg";
        } else if (strstr(full_path, ".doc") || strstr(full_path, ".docx")) {
            content_type = "application/msword";
        } else if (strstr(full_path, ".pdf")) {
            content_type = "application/pdf";
        }

        // header de la respuesta
        snprintf(header, sizeof(header),
                 "HTTP/1.1 200 OK\r\n"
                 "Date: %s\r\n"
                 "Server: %s\r\n"
                 "Last-Modified: %s\r\n"
                 "Content-Length: %ld\r\n"
                 "Connection: close\r\n"
                 "Content-Type: %s\r\n"
                 "\r\n",
                 date, config.server_signature, last_modified, file_stat.st_size, content_type);

        // enviar el header
        ssize_t length, bytes_written, write_ret;

        length = strlen(header);
        bytes_written = 0;
        while (bytes_written < length) {
            write_ret = write(client_fd, header + bytes_written, length - bytes_written);
            if (write_ret < 0) {
                if (EPIPE == errno) {
                    log_warning("Client closed the connection before receiving a response.");
                } else {
                    log_error(strerror(errno));
                }
                close(file_fd);
                goto clean_argv;
            }
            bytes_written += write_ret;
        }

        // enviar el contenudo del fichero
        char buffer[BUFF_SIZE];
        while ((length = read(file_fd, buffer, sizeof(buffer))) > 0) {
            bytes_written = 0;
            while (bytes_written < length) {
                write_ret = write(client_fd, buffer + bytes_written, length - bytes_written);
                if (write_ret < 0) {
                    if (EPIPE == errno) {
                        log_warning("Client closed the connection before receiving a response.");
                    } else {
                        log_error(strerror(errno));
                    }
                    close(file_fd);
                    goto clean_argv;
                }
                bytes_written += write_ret;
            }
        }

        close(file_fd);
    } else {
        char *response = cgi_get_script(argv, client_fd);

        if (NULL == response) {
            send_http_response(client_fd, 500, "text/html", "<h1>500 Internal Server Error</h1>");
            goto clean_argv;
        }
        pthread_cleanup_push(free, (void *)response);

        char header[512];
        char date[64];
        ssize_t length = strlen(response);

        time_t now = time(NULL);
        struct tm tm;
        gmtime_r(&now, &tm);
        strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", &tm);

        // header de la respuesta
        snprintf(header, sizeof(header),
                 "HTTP/1.1 200 OK\r\n"
                 "Date: %s\r\n"
                 "Server: %s\r\n"
                 "Content-Length: %ld\r\n"
                 "Connection: close\r\n"
                 "Content-Type: text/plain\r\n"
                 "\r\n",
                 date, config.server_signature, length);

        // enviar el header
        ssize_t bytes_written, write_ret;

        length = strlen(header);
        bytes_written = 0;
        while (bytes_written < length) {
            write_ret = write(client_fd, header + bytes_written, length - bytes_written);
            if (write_ret < 0) {
                if (EPIPE == errno) {
                    log_warning("Client closed the connection before receiving a response.");
                } else {
                    log_error(strerror(errno));
                }
                goto clean;
            }
            bytes_written += write_ret;
        }

        length = strlen(response);
        bytes_written = 0;
        while (bytes_written < length) {
            write_ret = write(client_fd, response + bytes_written, length - bytes_written);
            if (write_ret < 0) {
                if (EPIPE == errno) {
                    log_warning("Client closed the connection before receiving a response.");
                } else {
                    log_error(strerror(errno));
                }
                goto clean;
            }
            bytes_written += write_ret;
        }
    clean:
        pthread_cleanup_pop(1);
    }
clean_argv:
    pthread_cleanup_pop(1);
}

void handle_OPTIONS_request(int client_fd, const char *path) {
    char response[MAX_URI_SIZE];
    ssize_t bytes_written, length, write_ret;

    if (strcmp(path, "*") == 0) {
        sprintf(response, "HTTP/1.1 200 OK\r\n"
                          "Allow: GET,POST,OPTIONS\r\n"
                          "\r\n");
    } else {
        struct stat file_stat;
        char full_path[MAX_FULL_PATH];

        if (-1 == get_full_path(client_fd, full_path, path)) {
            log_info("Requested path wasn't valid.");
            return;
        }

        if (stat(full_path, &file_stat) < 0) {
            send_http_response(client_fd, 404, "text/html", "<h1>404 Not Found</h1>");
            return;
        }

        bzero(response, MAX_URI_SIZE);
        if (NULL == strstr(full_path, ".php") && NULL == strstr(full_path, ".py")) {
            sprintf(response, "HTTP/1.1 200 OK\r\n"
                              "Allow: GET,OPTIONS\r\n"
                              "\r\n");
        } else {
            sprintf(response, "HTTP/1.1 200 OK\r\n"
                              "Allow: GET,POST,OPTIONS\r\n"
                              "\r\n");
        }
    }

    length = strlen(response);
    bytes_written = 0;
    while (bytes_written < length) {
        write_ret = write(client_fd, response + bytes_written, length - bytes_written);
        if (write_ret < 0) {
            if (EPIPE == errno) {
                log_warning("Client closed the connection before receiving a response.");
            } else {
                log_error(strerror(errno));
            }
            return;
        }
        bytes_written += write_ret;
    }
}

void handle_POST_request(int client_fd, const char *path) {
    struct stat file_stat;

    char full_path[MAX_FULL_PATH];

    if (-1 == get_full_path(client_fd, full_path, path)) {
        log_info("Requested path wasn't valid.");
        return;
    }

    char **argv = parse_script_args(full_path);
    pthread_cleanup_push(args_free, (void *)argv);

    if (stat(full_path, &file_stat) < 0) {
        send_http_response(client_fd, 404, "text/html", "<h1>404 Not Found</h1>");
        goto clean_argv;
    }

    if (NULL == argv) {
        send_http_response(client_fd, 501, "text/html", "<h1>501 Not Implemented</h1>");
        goto clean_argv;
    }

    char *response = cgi_post_script(argv, client_fd);

    if (NULL == response) {
        send_http_response(client_fd, 500, "text/html", "<h1>500 Internal Server Error</h1>");
        goto clean_argv;
    }
    pthread_cleanup_push(free, (void *)response);

    char header[512];
    char date[64];
    ssize_t length = strlen(response);

    time_t now = time(NULL);
    struct tm tm;
    gmtime_r(&now, &tm);
    strftime(date, sizeof(date), "%a, %d %b %Y %H:%M:%S GMT", &tm);

    // header de la respuesta
    snprintf(header, sizeof(header),
             "HTTP/1.1 200 OK\r\n"
             "Date: %s\r\n"
             "Server: %s\r\n"
             "Content-Length: %ld\r\n"
             "Connection: close\r\n"
             "Content-Type: text/plain\r\n"
             "\r\n",
             date, config.server_signature, length);

    // enviar el header
    ssize_t bytes_written, write_ret;

    length = strlen(header);
    bytes_written = 0;
    while (bytes_written < length) {
        write_ret = write(client_fd, header + bytes_written, length - bytes_written);
        if (write_ret < 0) {
            if (EPIPE == errno) {
                log_warning("Client closed the connection before receiving a response.");
            } else {
                log_error(strerror(errno));
            }
            goto clean;
        }
        bytes_written += write_ret;
    }

    length = strlen(response);
    bytes_written = 0;
    while (bytes_written < length) {
        write_ret = write(client_fd, response + bytes_written, length - bytes_written);
        if (write_ret < 0) {
            if (EPIPE == errno) {
                log_warning("Client closed the connection before receiving a response.");
            } else {
                log_error(strerror(errno));
            }
            goto clean;
        }
        bytes_written += write_ret;
    }

clean:
    pthread_cleanup_pop(1);
clean_argv:
    pthread_cleanup_pop(1);
}

void handle_http_request(int client_fd) {
    char buffer[BUFF_SIZE];
    ssize_t bytes_read, read_ret;
    char cr, lf, header = 1;

    cr = 0;
    lf = 0;
    bytes_read = 0;
    bzero(buffer, BUFF_SIZE);

    // Lee la primera línea de la petición, la que contiene el verbo
    // Byte a byte para evitar leer parte del cuerpo accidentalmente
    while (!(cr && lf) && bytes_read < (BUFF_SIZE - 1)) {
        read_ret = read(client_fd, buffer + bytes_read, 1);
        if (read_ret == 0) {
            if (bytes_read) {
                send_http_response(client_fd, 400, "text/html", "<h1>400 Bad Request</h1>");
                log_error("Connection closed while receiving a request.");
            }
            return;
        }
        if (read_ret < 0) {
            if (EAGAIN == errno || EWOULDBLOCK == errno) {
                log_warning("Client exceeded socket timeout.");
            } else {
                log_error(strerror(errno));
                send_http_response(client_fd, 500, "text/html", "<h1>500 Internal Server Error</h1>");
            }
            return;
        }

        if (cr) {
            if ('\n' == buffer[bytes_read]) {
                lf = 1;
            } else {
                cr = 0;
            }
        }
        if ('\r' == buffer[bytes_read]) {
            cr = 1;
        }

        bytes_read += read_ret;
    }

    buffer[bytes_read] = '\0';

    char method[8], path[MAX_URI_SIZE], protocol[16];
    int ret = sscanf(buffer, "%7s %255s %15s", method, path, protocol);

    if (ret != 3) {
        send_http_response(client_fd, 400, "text/html", "<h1>400 Bad Request</h1>");
        return;
    }

    // log_info("Received HTTP request: %s %s", method, path);

    // Lee el resto de la cabecera hasta encontrar la línea con solo \r\n
    // También byte a byte, para evitar leer parte del cuerpo
    while (header) {
        cr = 0;
        lf = 0;
        bytes_read = 0;
        bzero(buffer, strlen(buffer));
        while (!(cr && lf) && bytes_read < (BUFF_SIZE - 1)) {
            read_ret = read(client_fd, buffer + bytes_read, 1);
            if (read_ret == 0) {
                if (bytes_read) {
                    send_http_response(client_fd, 400, "text/html", "<h1>400 Bad Request</h1>");
                    log_error("Connection closed while receiving a request.");
                }
                return;
            }
            if (read_ret < 0) {
                if (EAGAIN == errno || EWOULDBLOCK == errno) {
                    log_warning("Client exceeded socket timeout.");
                } else {
                    log_error(strerror(errno));
                    send_http_response(client_fd, 500, "text/html", "<h1>500 Internal Server Error</h1>");
                }
                return;
            }

            if (cr) {
                if ('\n' == buffer[bytes_read]) {
                    lf = 1;
                } else {
                    cr = 0;
                }
            }
            if ('\r' == buffer[bytes_read]) {
                cr = 1;
            }

            bytes_read += read_ret;
        }

        if (cr && lf && strlen(buffer) == 2) {
            header = 0;
        }
    }

    if (strcmp(method, "GET") == 0) {
        handle_GET_request(client_fd, path);
    } else if (strcmp(method, "OPTIONS") == 0) {
        handle_OPTIONS_request(client_fd, path);
    } else if (strcmp(method, "POST") == 0) {
        handle_POST_request(client_fd, path);
    } else {
        send_http_response(client_fd, 501, "text/html", "<h1>501 Not Implemented</h1>");
    }
}
