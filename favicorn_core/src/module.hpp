#ifndef MODULE
#define MODULE

namespace extension {
	inline PyMethodDef ExtensionMethods[] = {
	    {NULL, NULL, 0, NULL}
	};
	inline struct PyModuleDef core_module = {
	    PyModuleDef_HEAD_INIT,
	    "favicorn_core",
	    NULL,
	    -1,
	    NULL
	};
};
#endif