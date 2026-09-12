#include "apexforge_native.h"

#include <stddef.h>

#if !defined(_M_X64)
#error P12.4F-C requires the MSVC x64 target
#endif

#define APEXFORGE_INTERNAL_LIFECYCLE_CAPACITY 64u

#define APEXFORGE_INTERNAL_STATUS_INVALID_RESOURCE ((apexforge_status_t)1)
#define APEXFORGE_INTERNAL_STATUS_UNKNOWN_RESOURCE ((apexforge_status_t)2)
#define APEXFORGE_INTERNAL_STATUS_RESOURCE_KIND_MISMATCH ((apexforge_status_t)3)
#define APEXFORGE_INTERNAL_STATUS_BUFFER_LENGTH_MISMATCH ((apexforge_status_t)4)
#define APEXFORGE_INTERNAL_STATUS_REGISTRY_FULL ((apexforge_status_t)5)

typedef enum apexforge_internal_resource_kind {
    APEXFORGE_INTERNAL_RESOURCE_NONE = 0,
    APEXFORGE_INTERNAL_RESOURCE_HANDLE = 1,
    APEXFORGE_INTERNAL_RESOURCE_BUFFER = 2
} apexforge_internal_resource_kind;

typedef void (*apexforge_internal_disposer_fn)(void* resource, uint64_t length, void* context);

typedef struct apexforge_internal_lifecycle_entry {
    void* resource;
    uint64_t length;
    apexforge_internal_resource_kind kind;
    int live;
    apexforge_internal_disposer_fn disposer;
    void* context;
} apexforge_internal_lifecycle_entry;

static apexforge_internal_lifecycle_entry apexforge_internal_registry[APEXFORGE_INTERNAL_LIFECYCLE_CAPACITY];

static apexforge_internal_lifecycle_entry* apexforge_internal_find_resource(void* resource)
{
    size_t i;
    for (i = 0u; i < APEXFORGE_INTERNAL_LIFECYCLE_CAPACITY; ++i) {
        if (apexforge_internal_registry[i].resource == resource) {
            return &apexforge_internal_registry[i];
        }
    }
    return NULL;
}

static apexforge_internal_lifecycle_entry* apexforge_internal_find_free_slot(void)
{
    size_t i;
    for (i = 0u; i < APEXFORGE_INTERNAL_LIFECYCLE_CAPACITY; ++i) {
        if (apexforge_internal_registry[i].resource == NULL) {
            return &apexforge_internal_registry[i];
        }
    }
    return NULL;
}

static apexforge_status_t apexforge_internal_register_resource(
    void* resource,
    uint64_t length,
    apexforge_internal_resource_kind kind,
    apexforge_internal_disposer_fn disposer,
    void* context)
{
    apexforge_internal_lifecycle_entry* entry;
    if (resource == NULL) {
        return APEXFORGE_INTERNAL_STATUS_INVALID_RESOURCE;
    }
    entry = apexforge_internal_find_resource(resource);
    if (entry != NULL) {
        if (entry->live) {
            return APEXFORGE_INTERNAL_STATUS_INVALID_RESOURCE;
        }
        entry->length = length;
        entry->kind = kind;
        entry->live = 1;
        entry->disposer = disposer;
        entry->context = context;
        return APEXFORGE_STATUS_OK;
    }
    entry = apexforge_internal_find_free_slot();
    if (entry == NULL) {
        return APEXFORGE_INTERNAL_STATUS_REGISTRY_FULL;
    }
    entry->resource = resource;
    entry->length = length;
    entry->kind = kind;
    entry->live = 1;
    entry->disposer = disposer;
    entry->context = context;
    return APEXFORGE_STATUS_OK;
}

apexforge_status_t apexforge_internal_register_handle(
    apexforge_handle_t handle,
    apexforge_internal_disposer_fn disposer,
    void* context)
{
    return apexforge_internal_register_resource(
        handle,
        0u,
        APEXFORGE_INTERNAL_RESOURCE_HANDLE,
        disposer,
        context);
}

apexforge_status_t apexforge_internal_register_buffer(
    void* data,
    uint64_t length,
    apexforge_internal_disposer_fn disposer,
    void* context)
{
    return apexforge_internal_register_resource(
        data,
        length,
        APEXFORGE_INTERNAL_RESOURCE_BUFFER,
        disposer,
        context);
}

static apexforge_status_t apexforge_internal_release_resource(
    void* resource,
    uint64_t length,
    apexforge_internal_resource_kind expected_kind)
{
    apexforge_internal_lifecycle_entry* entry;
    apexforge_internal_disposer_fn disposer;
    void* context;
    uint64_t registered_length;

    if (resource == NULL) {
        return APEXFORGE_INTERNAL_STATUS_INVALID_RESOURCE;
    }

    entry = apexforge_internal_find_resource(resource);
    if (entry == NULL) {
        return APEXFORGE_INTERNAL_STATUS_UNKNOWN_RESOURCE;
    }
    if (!entry->live) {
        return APEXFORGE_INTERNAL_STATUS_UNKNOWN_RESOURCE;
    }
    if (entry->kind != expected_kind) {
        return APEXFORGE_INTERNAL_STATUS_RESOURCE_KIND_MISMATCH;
    }
    if (expected_kind == APEXFORGE_INTERNAL_RESOURCE_BUFFER && entry->length != length) {
        return APEXFORGE_INTERNAL_STATUS_BUFFER_LENGTH_MISMATCH;
    }

    disposer = entry->disposer;
    context = entry->context;
    registered_length = entry->length;

    entry->resource = NULL;
    entry->length = 0u;
    entry->kind = APEXFORGE_INTERNAL_RESOURCE_NONE;
    entry->live = 0;
    entry->disposer = NULL;
    entry->context = NULL;

    if (disposer != NULL) {
        disposer(resource, registered_length, context);
    }

    return APEXFORGE_STATUS_OK;
}

apexforge_status_t apexforge_internal_release_handle(apexforge_handle_t handle)
{
    return apexforge_internal_release_resource(
        handle,
        0u,
        APEXFORGE_INTERNAL_RESOURCE_HANDLE);
}

apexforge_status_t apexforge_internal_release_buffer(void* data, uint64_t length)
{
    return apexforge_internal_release_resource(
        data,
        length,
        APEXFORGE_INTERNAL_RESOURCE_BUFFER);
}
