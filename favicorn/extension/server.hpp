#include <Python.h>
#include <structmember.h>
#include <new>
#include <exception>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <iostream>


class Server {
private:
    sockaddr_in addr;
    int server_id;
    char buffer[1500];
public:
    Server(
        const uint32_t host,
        const uint16_t port
    ) : addr{0}, server_id{0}, buffer{""} {
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = htonl(host);
        addr.sin_port = htons(port);
    };
    int start() {
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
    void receive() const {
        int client = accept(server_id, nullptr, 0);
        if (client < 0) return;
        recv(client, (char*) buffer, sizeof(buffer), 0);
        const char* res = "HTTP/1.1 200 OK\r\nContent-Length:0\r\n\r\n";
        send(client, res, strlen(res), 0);
        close(client);
    };
    const char* get_buffer() const {
        return buffer;
    };
    ~Server() const {
        if (server_id <= 0) return;
        close(server_id);
    };

};
typedef struct {
    PyObject_HEAD
    Server*    m_myclass;
} PyServer;

int PyServer_init(
	PyObject* self,
	PyObject* args,
	PyObject* kwds
) {
    int port;
    PyObject* ip_address = nullptr;
    int status = PyArg_ParseTuple(
        args,
        "Oi",
        &ip_address,
        &port
    );
    if (status < 0) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid args");
        return -1;
    }
    PyObject* ipaddress_module_name = PyUnicode_FromString(
        (char*)"ipaddress"
    );
    PyObject* ipaddress_module = PyImport_Import(ipaddress_module_name);
    PyObject* ip_v4_class = PyObject_GetAttrString(
        ipaddress_module,
        (char*)"IPv4Address"
    );
    status = PyObject_IsInstance(ip_address, ip_v4_class);
    if (status == -1) return -1;
    if (status == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Host argument must be instance of IPv4Address class");
        return -1;
    };
    PyObject* fn = PyObject_GetAttrString(ip_address, "__int__");    
    if (fn == NULL) {
        return -1;
    };
    PyObject* result = PyObject_CallNoArgs(fn);
    if (result == NULL) {
        return -1;
    };
    long host = PyLong_AsLong(result);
    PyServer* m = (PyServer*)self;

    m -> m_myclass = (Server*)PyObject_Malloc(sizeof(Server));
    if(!m -> m_myclass){
        PyErr_SetString(PyExc_RuntimeError, "Memory allocation failed");
        return -1;
    }
    try {
        new (m -> m_myclass) Server(
            host,
            port
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
PyObject* PyServer_new(
	PyTypeObject* subtype,
	PyObject *args,
	PyObject *kwds
) {
    PyServer *self;
    self = (PyServer*) subtype -> tp_alloc(subtype, 0);
    if (self != NULL) {
        self -> m_myclass = NULL; 
    }
    return (PyObject*) self;
};
void PyServer_dealloc(PyServer* self) {
    PyTypeObject *tp = Py_TYPE(self);

    PyServer* m = reinterpret_cast<PyServer*>(self);

    if (m -> m_myclass) {
        m -> m_myclass -> ~Server();
        PyObject_Free(m -> m_myclass);
    }

    tp -> tp_free(self);
    Py_DECREF(tp);
};
PyObject* PyServer_start(PyObject *self, PyObject *args) {
    assert(self);

    PyServer* _self = reinterpret_cast<PyServer*>(self);
    unsigned long val = _self -> m_myclass -> start();
    return PyLong_FromUnsignedLong(val);
};
PyObject* PyServer_receive(PyObject *self, PyObject *args) {
    assert(self);

    PyServer* _self = reinterpret_cast<PyServer*>(self);
    _self -> m_myclass -> receive();
    return PyUnicode_FromString(_self -> m_myclass -> get_buffer());
};

static PyMethodDef PyServer_methods[] = {
    {
        "start",
        (PyCFunction)PyServer_start,
        METH_NOARGS,
        PyDoc_STR("Create socket and bind to specified address")
    },
    {
        "receive",
        (PyCFunction)PyServer_receive,
        METH_NOARGS,
        NULL
    },
    {NULL, NULL} /* Sentinel */
};

static struct PyMemberDef PyServer_members[] = {
    {NULL} /* Sentinel */
};

static PyType_Slot PyServer_slots[] = {
    {Py_tp_new, (void*)PyServer_new},
    {Py_tp_init, (void*)PyServer_init},
    {Py_tp_dealloc, (void*)PyServer_dealloc},
    {Py_tp_members,  PyServer_members},
    {Py_tp_methods, PyServer_methods},
    {0, 0}
};

static PyType_Spec server_spec = {
    "Server",                                  // name
    sizeof(PyServer) + sizeof(Server),    // basicsize
    0,                                          // itemsize
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   // flags
    PyServer_slots                               // slots
};