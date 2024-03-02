#include "./loop.hpp"

#include <chrono>
#include <iostream>
#include <optional>
#include <ostream>
#include <stdexcept>
#include <thread>

#include "uv.h"

UVLoop::UVLoop() {
    int error = uv_loop_init(this);
    if (error != 0) {
        throw std::runtime_error(uv_strerror(error));
    };
};

void UVLoop::run_forever() noexcept {
    while (!shouldStop) {
        uv_run(this, UV_RUN_NOWAIT);
    };
};

void UVLoop::stop() noexcept {
    shouldStop = true; 
};

void on_uv_walk(uv_handle_t *handle, void *arg) { uv_close(handle, NULL); }

std::optional<std::runtime_error> UVLoop::close() noexcept {
    uv_walk(this, on_uv_walk, NULL);
    int error = uv_run(this, UV_RUN_DEFAULT);
    if (error != 0) {
        return std::runtime_error(uv_strerror(error));
    };
    error = uv_loop_close(this);
    if (error != 0) {
        return std::runtime_error(uv_strerror(error));
    }
    return {};
};
