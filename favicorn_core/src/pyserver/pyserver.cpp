#include "src/pyserver/pyserver.hpp"
#include "src/module.hpp"
#include <vector>


static PyObject* scope_type = NULL;

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
    HTTPRequest* request = NULL;
    unsigned short socketId;
    std::tie(request, socketId) = _self -> m_myclass -> receive();
    if (request == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }
    PyObject* module = PyState_FindModule(&extension::core_module);
    PyObject* manager_class = PyObject_GetAttrString(module, "ASGIManager");
    PyObject* asgi_manager = PyObject_CallFunction(
        manager_class,
        "HO",
        socketId,
        PyCapsule_New((void*)request, NULL, NULL)
    );
    delete request;
    return asgi_manager;
};