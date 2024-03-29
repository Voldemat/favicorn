#ifndef INCLUDE_HTTP_PARSER_H_
#define INCLUDE_HTTP_PARSER_H_

#include <cstddef>
#include <tuple>
#include <unordered_map>
#include <memory>
#include "llhttp.h"


struct HTTPRequest {
	std::unique_ptr<char[]> url;
	char method[6] = "\n";
	char http_version[4] = "\n";
	std::unordered_map<const char*, const char*> headers;

	HTTPRequest();
};

struct parse_settings_t : llhttp_settings_t {
	HTTPRequest* request;
	char* current_header_key;
};
class HTTPParser {
	llhttp_t parser;
	parse_settings_t settings;
public:
	HTTPParser();
	std::tuple<HTTPRequest*, const char*> parse_request(
		const char* buffer,
		size_t length
	);

};
#endif
