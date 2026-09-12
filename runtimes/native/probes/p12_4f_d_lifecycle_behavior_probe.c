#include "apexforge_native.h"
#if !defined(_M_X64)
#error P12.4F-D requires the MSVC x64 target
#endif
typedef void (*apexforge_internal_disposer_fn)(void* resource, uint64_t length, void* context);
extern apexforge_status_t apexforge_internal_register_handle(apexforge_handle_t handle, apexforge_internal_disposer_fn disposer, void* context);
extern apexforge_status_t apexforge_internal_register_buffer(void* data, uint64_t length, apexforge_internal_disposer_fn disposer, void* context);
__declspec(dllimport) void __stdcall ExitProcess(unsigned int exit_code);
static int dispose_count;
static void disposer(void* resource, uint64_t length, void* context){(void)resource;(void)length;(void)context;++dispose_count;}
static unsigned int run_tests(void){int h=11;int b=22;int u=33;int cx=44;apexforge_status_t s;s=apexforge_release_handle((apexforge_handle_t)0);if(s==APEXFORGE_STATUS_OK)return 10u;s=apexforge_release_handle(&u);if(s==APEXFORGE_STATUS_OK)return 11u;s=apexforge_internal_register_handle(&h,disposer,&cx);if(s!=APEXFORGE_STATUS_OK)return 20u;s=apexforge_release_buffer(&h,0u);if(s==APEXFORGE_STATUS_OK||dispose_count!=0)return 21u;s=apexforge_release_handle(&h);if(s!=APEXFORGE_STATUS_OK||dispose_count!=1)return 22u;s=apexforge_release_handle(&h);if(s==APEXFORGE_STATUS_OK||dispose_count!=1)return 23u;s=apexforge_internal_register_buffer(&b,16u,disposer,&cx);if(s!=APEXFORGE_STATUS_OK)return 30u;s=apexforge_release_buffer(&b,15u);if(s==APEXFORGE_STATUS_OK||dispose_count!=1)return 31u;s=apexforge_release_buffer(&b,16u);if(s!=APEXFORGE_STATUS_OK||dispose_count!=2)return 32u;s=apexforge_release_buffer(&b,16u);if(s==APEXFORGE_STATUS_OK||dispose_count!=2)return 33u;s=apexforge_internal_register_handle(&h,disposer,&cx);if(s!=APEXFORGE_STATUS_OK)return 40u;s=apexforge_release_handle(&h);if(s!=APEXFORGE_STATUS_OK||dispose_count!=3)return 41u;return 0u;}
void p12_4f_d_entry(void){ExitProcess(run_tests());}
