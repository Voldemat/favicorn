#include "src/pyasgi/pyasgi.hpp"
#include <netinet/in.h>
#include <string>


static const auto& socketSend = send;

static const PyDictObject* buildHttpScope(const HTTPRequest* request) {
	PyObject* scope = PyDict_New();
    PyObject* scope_asgi = PyDict_New();
    std::vector<PyObject*> headers_tuples;
    for (const std::pair<const char*, const char*> item : request -> headers) {
        PyObject* key = PyUnicode_FromString(item.first);
        PyObject* value = PyUnicode_FromString(item.second);
        PyObject* tuple = PyTuple_Pack(2, key, value);
        headers_tuples.push_back(tuple);
    };
    PyObject* headers = PyTuple_New(headers_tuples.size());
    for (int index = 0; index < headers_tuples.size(); ++index){
        PyTuple_SetItem(headers, index, headers_tuples[index]);
    };
    PyDict_SetItemString(scope_asgi, "version", PyUnicode_FromString("3.0"));
    PyDict_SetItemString(scope_asgi, "spec_version", PyUnicode_FromString("2.3"));
    PyDict_SetItemString(scope, "path", PyUnicode_FromString(request -> url.get()));
    PyDict_SetItemString(scope, "type", PyUnicode_FromString("type"));
    PyDict_SetItemString(scope, "method", PyUnicode_FromString(request -> method));
    PyDict_SetItemString(scope, "scheme", PyUnicode_FromString("http"));
    PyDict_SetItemString(scope, "headers", headers);
    return (const PyDictObject*)scope;
};


ASGIManager::ASGIManager(const unsigned short& sId, const HTTPRequest* req) : socketId{sId} {
	scope = buildHttpScope(req);
};

const PyDictObject* ASGIManager::get_scope() const noexcept {
	return scope;
};

PyDictObject* ASGIManager::receive() const noexcept {
	PyObject* event = PyDict_New();
	PyDict_SetItemString(event, "type", PyUnicode_FromString("http.request"));
	PyDict_SetItemString(event, "body", PyUnicode_FromString("some data"));
	PyDict_SetItemString(event, "more_body", Py_False);
	return (PyDictObject*) event;
};

void ASGIManager::send(const BaseSendEvent& event) const noexcept {
	switch (event.type) {
        case SendEventType::HTTP_RESPONSE_START: {
            const ResStartEvent& start_event = (const ResStartEvent&) event;
            std::string buffer = (
                "HTTP/1.1 " + std::to_string(start_event.status) + "\r\n"
            );
            for (
                const std::tuple<const char*, const char*>& item : start_event.headers
            ) {
                buffer += std::get<0>(item);
                buffer += ": ";
                buffer += std::get<1>(item);
                buffer += "\r\n";
            };
            socketSend(socketId, buffer.c_str(), buffer.length(), 0);
        };
        case SendEventType::HTTP_RESPONSE_BODY: {
            const ResBodyEvent& body_event = (const ResBodyEvent&) event;
            if (body_event.more_body) {
                socketSend(socketId, body_event.body, strlen(body_event.body), 0);
            } else {
                unsigned int length = strlen(body_event.body);
                char buffer[length + 2];
                memcpy((void*) buffer, body_event.body, length);
                buffer[length + 1] = '\r';
                buffer[length + 2] = '\n';
                socketSend(socketId, buffer, length + 2, 0);
                close(socketId);
            }
            break;
        };
    };
};

PyObject* PyASGI_new(PyTypeObject* subtype, PyObject *args, PyObject *kwds) {
	PyASGI *self;
    self = (PyASGI*) subtype -> tp_alloc(subtype, 0);
    if (self != NULL) {
        self -> m_myclass = NULL; 
    }
    return (PyObject*) self;
};
int PyASGI_init(PyObject* self, PyObject* args, PyObject* kwds) {
	unsigned short socketId;
	PyObject* capsule = nullptr;
    int status = PyArg_ParseTuple(
        args,
        "HO",
        &socketId,
        &capsule
    );
    if (status < 0 || !PyCapsule_CheckExact(capsule)) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid args");
        return -1;
    };
    HTTPRequest* req = (HTTPRequest*) PyCapsule_GetPointer(capsule, NULL);
    PyASGI* m = (PyASGI*)self;
    m -> m_myclass = (ASGIManager*)PyObject_Malloc(sizeof(ASGIManager));
    if(!m -> m_myclass){
        PyErr_SetString(PyExc_RuntimeError, "Memory allocation failed");
        return -1;
    }
    try {
        new (m -> m_myclass) ASGIManager(
            socketId,
            req
        );
    } catch (const std::exception& ex) {
        PyObject_Free(m -> m_myclass);
        m -> m_myclass = NULL;
        PyErr_SetString(PyExc_RuntimeError, ex.what());
        return -1;
    } catch(...) {
        PyObject_Free(m -> m_myclass);
        m -> m_myclass = NULL;
        PyErr_SetString(PyExc_RuntimeError, "Initialization failed");
        return -1;
    }

    return 0;
};
void PyASGI_dealloc(PyASGI* self) {
	PyTypeObject *tp = Py_TYPE(self);

    PyASGI* m = reinterpret_cast<PyASGI*>(self);

    if (m -> m_myclass) {
        m -> m_myclass -> ~ASGIManager();
        PyObject_Free(m -> m_myclass);
    }

    tp -> tp_free(self);
    Py_DECREF(tp);
};
PyObject* PyASGI_get_scope(PyObject *self, PyObject* args) {
    PyASGI* pyasgi = reinterpret_cast<PyASGI*>(self);
	const PyDictObject* scope = pyasgi -> m_myclass -> get_scope();
	Py_INCREF(scope);
	return (PyObject*) scope;
};
PyObject* PyASGI_receive(PyObject *self, PyObject* args) {
	PyASGI* pyasgi = reinterpret_cast<PyASGI*>(self);
	return (PyObject*) pyasgi -> m_myclass -> receive();
};
PyObject* PyASGI_send(
	PyObject *self,
	PyObject* const *args,
	Py_ssize_t nargs
) {
    if (nargs != 1 || !PyDict_Check(args[0])) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid args");
        return Py_None;
    };
    PyASGI* pyasgi = reinterpret_cast<PyASGI*>(self);
    PyObject* event = args[0];
    PyObject* etype = PyDict_GetItemString(event, "type");
    const char* event_type = (const char*) PyUnicode_DATA(etype);
    if (strcmp(event_type, "http.response.start") == 0) {
        std::vector<std::tuple<const char*, const char*>> headers;
        PyObject* pyheaders = PyDict_GetItemString(event, "headers");
        PyObject* pyheaders_iter_fn = PyObject_GetAttrString(
            pyheaders,
            "__iter__"
        );
        PyObject* pyheaders_iter = PyObject_CallNoArgs(pyheaders_iter_fn);
        PyObject* item;
        while ((item = PyIter_Next(pyheaders_iter))) {
            PyObject* pykey = PyTuple_GET_ITEM(item, 0);
            const char* key = (const char*) PyUnicode_DATA(pykey);
            PyObject* pyvalue = PyTuple_GET_ITEM(item, 1);
            const char* value = (const char*) PyUnicode_DATA(pyvalue);
            headers.push_back(std::make_tuple(key, value));
        };
        PyObject* pystatus = PyDict_GetItemString(event, "status");
        unsigned short status = (unsigned short)(PyLong_AsLong(pystatus));
        const ResStartEvent start_event(status, headers);
        pyasgi -> m_myclass -> send(start_event);
    } else if (strcmp(event_type, "http.response.body") == 0) {
        const ResBodyEvent body_event("", false);
        pyasgi -> m_myclass -> send(body_event);
    } else {
        PyErr_SetString(PyExc_RuntimeError, "Invalid event type");
    };
    Py_INCREF(Py_None);
    return Py_None;
};
