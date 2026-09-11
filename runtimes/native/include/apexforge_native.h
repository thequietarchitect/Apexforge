#ifndef APEXFORGE_NATIVE_H
#define APEXFORGE_NATIVE_H

#include <stdint.h>

#define APEXFORGE_NATIVE_ABI_PROFILE "apexforge.win-x64-managed-native-abi/v1"
#define APEXFORGE_NATIVE_EXPORT_LIFECYCLE_PROFILE "apexforge.win-x64-native-export-lifecycle/v1"

#ifdef __cplusplus
extern "C" {
#endif

typedef int32_t apexforge_status_t;
typedef void* apexforge_handle_t;

#define APEXFORGE_STATUS_OK ((apexforge_status_t)0)

apexforge_status_t apexforge_release_handle(apexforge_handle_t handle);
apexforge_status_t apexforge_release_buffer(void* data, uint64_t length);

#ifdef __cplusplus
}
#endif

#endif
