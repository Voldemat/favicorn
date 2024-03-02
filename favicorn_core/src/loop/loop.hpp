#ifndef UVLOOP
#define UVLOOP

#include <optional>
#include <stdexcept>
#include "uv.h"

class UVLoop: public uv_loop_t {
private:
    bool shouldStop = false;
public:
    explicit UVLoop();
    void run_forever() noexcept;
    void stop() noexcept;
    std::optional<std::runtime_error> close() noexcept;
};
#endif
