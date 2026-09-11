#include "apexforge_native.h"

#if !defined(_M_X64)
#error P12.4E requires the MSVC x64 target
#endif

extern apexforge_status_t apexforge_internal_release_handle(apexforge_handle_t handle);
extern apexforge_status_t apexforge_internal_release_buffer(void* data, uint64_t length);

apexforge_status_t apexforge_release_handle(apexforge_handle_t handle)
{
    return apexforge_internal_release_handle(handle);
}

apexforge_status_t apexforge_release_buffer(void* data, uint64_t length)
{
    return apexforge_internal_release_buffer(data, length);
}
