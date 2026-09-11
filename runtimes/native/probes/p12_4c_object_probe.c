#include "apexforge_native.h"

#if !defined(_M_X64)
#error P12.4C requires the MSVC x64 target
#endif

typedef char apexforge_p12_4c_status_width[(sizeof(apexforge_status_t) == 4) ? 1 : -1];
typedef char apexforge_p12_4c_handle_width[(sizeof(apexforge_handle_t) == 8) ? 1 : -1];
typedef char apexforge_p12_4c_length_width[(sizeof(uint64_t) == 8) ? 1 : -1];

apexforge_status_t apexforge_p12_4c_object_probe(void)
{
    return APEXFORGE_STATUS_OK;
}
