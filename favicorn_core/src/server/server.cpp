#include <unistd.h>
#include <iostream>
#include <llhttp.h>

#include "src/server/server.hpp"
#include "src/http_parser/http_parser.hpp"


Server::Server(
    const uint32_t host,
    const uint16_t port
) : addr{0}, server_id{0}, buffer{""} {
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
void Server::receive() const {
    int client = accept(server_id, nullptr, 0);
    if (client < 0) return;
    recv(client, (char*) buffer, sizeof(buffer), 0);
    HTTPRequest* request;
    const char* error_msg;
    std::tie(request, error_msg) = parse_request(
        buffer,
        strlen(buffer)
    );
    if (request == NULL) {
        std::cout << error_msg << std::endl;
    } else {
        std::cout << "URL: " << request -> url << std::endl;
        std::cout << "Method: " << request -> method << std::endl;
        std::cout << "HTTP Version: " << request -> http_version << std::endl;
        std::cout << "Headers count: " << (request -> headers).size() << std::endl;
    };
    const char* res = "HTTP/1.1 200 OK\r\nContent-Length:0\r\n\r\n";
    send(client, res, strlen(res), 0);
    close(client);
    delete request;
};
const char* Server::get_buffer() const {
    return buffer;
};
Server::~Server() {
    if (server_id <= 0) return;
    close(server_id);
};
