#include "src/http_parser/http_parser.hpp"

int on_url(llhttp_t* parser, const char* buffer, size_t length) {
	HTTPRequest* request = ((parse_settings_t*) (parser -> settings)) -> request;
	request -> url = new char[length + 1];
	memcpy((void*)request -> url, buffer, length);
	return 0;
};

int on_method(llhttp_t* parser, const char* buffer, size_t length) {
	HTTPRequest* request = ((parse_settings_t*) (parser -> settings)) -> request;
	if (length > sizeof(request -> method) - 1) return -1;
	memcpy((void*)request -> method, buffer, length);
	return 0;
};

int on_version(llhttp_t* parser, const char* buffer, size_t length) {
	HTTPRequest* request = ((parse_settings_t*) (parser -> settings)) -> request;
	if (length > sizeof(request -> http_version) - 1) return -1;
	memcpy((void*)request -> http_version, buffer, length);
	return 0;
};
int on_header_field(llhttp_t* parser, const char* buffer, size_t length) {
	parse_settings_t* settings = (parse_settings_t*) parser -> settings;
	char* field = new char[length + 1];
	memcpy((void*) field, buffer, length);
	settings -> current_header_key = field;
	return 0;
};
int on_header_value(llhttp_t* parser, const char* buffer, size_t length) {
	parse_settings_t* settings = (parse_settings_t*) parser -> settings;
	if (settings -> current_header_key == nullptr) return -1;
	HTTPRequest* request = settings -> request;
	char* value = new char[length + 1];
	memcpy((void*) value, buffer, length);
	request -> headers[settings -> current_header_key] = value;
	return 0;
};
HTTPParser::HTTPParser() : parser{}, settings {} {
    llhttp_settings_init(&settings);
    settings.on_url = on_url;
    settings.on_method = on_method;
    settings.on_version = on_version;
    settings.on_header_field = on_header_field;
    settings.on_header_value = on_header_value;
    llhttp_init(&parser, HTTP_REQUEST, &settings);
};
std::tuple<HTTPRequest*, const char*>HTTPParser::parse_request(
	const char* buffer,
	size_t length
) {
	HTTPRequest* request = new HTTPRequest();
    settings.request = request;
    enum llhttp_errno err = llhttp_execute(&parser, buffer, strlen(buffer));
    if (err == HPE_OK) {
        return {request, NULL};
    } else {
    	char error_msg[200];
    	snprintf(
    		error_msg,
    		sizeof(error_msg),
    		"Parse Error: %s %s\n",
    		llhttp_errno_name(err),
    		parser.reason
    	);
    	return {NULL, error_msg};
    }
};

