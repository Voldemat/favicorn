#include "src/pyserver/pyserver.hpp"
#include <vector>


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
    const HTTPRequest* request = _self -> m_myclass -> receive();
    if (request == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }
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
    PyDict_SetItemString(scope, "path", PyUnicode_FromString(request -> url));
    PyDict_SetItemString(scope, "type", PyUnicode_FromString("http"));
    PyDict_SetItemString(scope, "method", PyUnicode_FromString(request -> method));
    PyDict_SetItemString(scope, "scheme", PyUnicode_FromString("http"));
    PyDict_SetItemString(scope, "headers", headers);
    delete request;
    return scope;
};