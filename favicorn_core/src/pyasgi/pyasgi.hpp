#ifndef PYASGI
#define PYASGI

#include "src/http_parser/http_parser.hpp"
#include "Python.h"
#include <structmember.h>
#include <vector>
#include <tuple>


enum SendEventType {
	HTTP_RESPONSE_START,
	HTTP_RESPONSE_BODY
};
struct BaseSendEvent {
    const SendEventType type;

    BaseSendEvent(const SendEventType type): type{type} {};
};
struct ResStartEvent : BaseSendEvent {
	const unsigned short status;
	const std::vector<std::tuple<const char*, const char*>> headers;

    ResStartEvent(
        const unsigned short status,
        const std::vector<std::tuple<const char*, const char*>> headers
    ) : BaseSendEvent{SendEventType::HTTP_RESPONSE_START}, status{status}, headers{headers} {};
};
struct ResBodyEvent : BaseSendEvent {
    const char* body;
    const bool more_body;

    ResBodyEvent(
        const char* body,
        const bool more_body
    ): 
        BaseSendEvent{SendEventType::HTTP_RESPONSE_BODY},
        body{body},
        more_body{more_body}
    {};
};

class ASGIManager {
	const unsigned short socketId;
	const PyDictObject* scope;
public:
	ASGIManager(const unsigned short& sId, const HTTPRequest* req);
	const PyDictObject* get_scope() const noexcept;
	PyDictObject* receive() const noexcept;
	void send(const BaseSendEvent& event) const noexcept;
};


typedef struct {
    PyObject_HEAD
    ASGIManager*    m_myclass;
} PyASGI;


int PyASGI_init(PyObject* self, PyObject* args, PyObject* kwds);
PyObject* PyASGI_new(PyTypeObject* subtype, PyObject *args, PyObject *kwds);
void PyASGI_dealloc(PyASGI* self);
PyObject* PyASGI_get_scope(PyObject *self, PyObject* args);
PyObject* PyASGI_receive(PyObject *self, PyObject* args);
PyObject* PyASGI_send(PyObject *self, PyObject* const *args, Py_ssize_t nargs);


static PyMethodDef PyASGI_methods[] = {
    {
        "get_scope",
        (PyCFunction)PyASGI_get_scope,
        METH_NOARGS,
        PyDoc_STR("Create socket and bind to specified address")
    },
    {
        "receive",
        (PyCFunction)PyASGI_receive,
        METH_NOARGS,
        NULL
    },
    {
        "send",
        (PyCFunction)PyASGI_send,
        METH_FASTCALL,
        NULL
    },
    {NULL, NULL} /* Sentinel */
};

static struct PyMemberDef PyASGI_members[] = {
    {NULL} /* Sentinel */
};

static PyType_Slot PyASGI_slots[] = {
    {Py_tp_new, (void*)PyASGI_new},
    {Py_tp_init, (void*)PyASGI_init},
    {Py_tp_dealloc, (void*)PyASGI_dealloc},
    {Py_tp_members,  PyASGI_members},
    {Py_tp_methods, PyASGI_methods},
    {0, 0}
};

static PyType_Spec pyasgi_spec = {
    "PyASGI",                                  // name
    sizeof(PyASGI) + sizeof(ASGIManager),    // basicsize
    0,                                          // itemsize
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,   // flags
    PyASGI_slots                               // slots
};

#endif