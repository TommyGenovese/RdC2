#ifndef HTTP_RESPONSE_H
#define HTTP_RESPONSE_H

#include <unistd.h>

// Struct para mapear los codigos de estado HTTP
typedef struct {
    int code;
    const char *message;
} http_status_t;

// envio respuesta http
int send_http_response(int connection_fd, int status_code, const char *content_type, const char *body);


// Funcion para obtener el mensaje correspondiente al codigo de estado
const char *get_status_message(int status_code);

void handle_http_request(int client_fd);

#endif
