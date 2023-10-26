#include <unistd.h>
#include <iostream>
#include <llhttp.h>

#include "src/server/server.hpp"


Server::Server(
    const uint32_t host,
    const uint16_t port
) : addr{0}, server_id{0}, buffer{""}, parser{} {
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(host);
    addr.sin_port = htons(port);
};
int Server::start() {
    server_id = socket(AF_INET, SOCK_STREAM, 0);
    if (server_id < 0) { return -1; };
    int bindStatus = bind(
        server_id,
        (struct sockaddr*) &addr, 
        sizeof(addr)
    );
    if (bindStatus < 0) {
        return -1;
    };
    listen(server_id, 5);
    return 0;
};
const HTTPRequest* Server::receive() {
    int client = accept(server_id, nullptr, 0);
    if (client < 0) return NULL;
    recv(client, (char*) buffer, sizeof(buffer), 0);
    const HTTPRequest* request;
    const char* error_msg;
    std::tie(request, error_msg) = parser.parse_request(
        buffer,
        strlen(buffer)
    );
    if (request == NULL) {
        std::cout << error_msg << std::endl;
    }
    const char* res = "HTTP/1.1 200 OK\r\nContent-Length:0\r\n\r\n";
    send(client, res, strlen(res), 0);
    close(client);
    return request;
};
Server::~Server() {
    if (server_id <= 0) return;
    close(server_id);
};
