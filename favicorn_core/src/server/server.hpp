#ifndef INCLUDE_SERVER_H_
#define INCLUDE_SERVER_H_

#include <netinet/in.h>
#include "src/http_parser/http_parser.hpp"

class Server {
private:
    sockaddr_in addr;
    int server_id;
    const char buffer[1500];
    HTTPParser parser;
public:
    Server(const uint32_t host, const uint16_t port);
    int start();
    const HTTPRequest* receive();
    ~Server();
};

#endif