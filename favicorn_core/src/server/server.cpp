#include "src/server/server.hpp"
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>


Server::Server(
    const uint32_t& host,
    const uint16_t& port
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
const std::tuple<HTTPRequest*, unsigned short> Server::receive() {
    int client = accept(server_id, nullptr, 0);
    if (client < 0) return {NULL, 0};
    recv(client, (char*) buffer, sizeof(buffer), 0);
    HTTPRequest* request = nullptr;
    const char* error_msg = nullptr;
    std::tie(request, error_msg) = parser.parse_request(
        buffer,
        strlen(buffer)
    );
    if (request == NULL) {
        printf("Request is NULL, error: %s\n", error_msg);
    }
    memset((void*)buffer, 0, sizeof(buffer));
    return {request, (unsigned short) client};
};
Server::~Server() {
    if (server_id <= 0) return;
    close(server_id);
};
