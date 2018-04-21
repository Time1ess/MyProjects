#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include <inttypes.h>
#include <math.h>
#include <stdlib.h>

#define _POSIX_C_SOURCE 200809L
#define N 10000000

int data_center_id;
int worker_id;
uint64_t global_ts;
uint64_t sqn;


uint64_t get_ts()
{
    struct timespec spec;
    clock_gettime(CLOCK_REALTIME, &spec);
    uint64_t res = spec.tv_sec * 1000 + spec.tv_nsec / 1.0e6;
    return res;
}

uint64_t gen_id()
{
    uint64_t uid = 0;
    uint64_t ts = get_ts();
    int is_full = 0;
    if(sqn == 4096)
    {
        while(ts == global_ts)
            ts = get_ts();
        is_full = 1;
    }
    if(global_ts < ts || is_full)
    {
        global_ts = ts;
        sqn = 0;
        //sqn = rand() % (2 << 12);
    }
    uid = uid | (ts << 22) | (data_center_id << 17) | (worker_id << 12) | sqn;
    sqn += 1;
    return uid;
}

void printb(uint64_t v)
{
    char bins[64];
    for(int i = 0; i < 64; i++)
        bins[i] = '0';
    int i = 63;
    while(v)
    {
        if(v & 0x1)
            bins[i--]= '1';
        else
            bins[i--]= '0';
        v >>= 1;
    }
    printf("0 ");
    for(int i = 1; i < 42; i++)
        printf("%c", bins[i]);
    printf(" ");
    for(int i = 42; i < 47; i++)
        printf("%c", bins[i]);
    printf(" ");
    for(int i = 47; i < 52; i++)
        printf("%c", bins[i]);
    printf(" ");
    for(int i = 52; i < 64; i++)
        printf("%c", bins[i]);
    printf("\n");
}

int main(void)
{
    data_center_id = 1;
    worker_id = 2;
    global_ts = 0;
    sqn = 0;
    uint64_t s = get_ts();
    for(int i = 0; i < N; i++)
        gen_id();
    uint64_t e = get_ts();
    printf("IDs per second: %lld, ID/ms: %.5f\n", 1000l * N / (e - s), 1.0 * (e-s) / N);
    return 0;
}
