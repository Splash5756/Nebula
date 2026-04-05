#include <stdio.h>
#include "python_bridge_mock.h"

// Python motorunun (Slave) çalışıp çalışmadığını takip eden sahte state
static int __python_slave_running = 0;

void nebula_python_init(void) {
    if (!__python_slave_running) {
        printf("[Python Bridge] Initializing Python VM in SLAVE mode...\n");
        printf("[Python Bridge] ALERT: Python's Global Interpreter Lock (GIL) and Event Loop are subordinated.\n");
        printf("[Python Bridge] Nebula is now the MASTER of context switching.\n");
        __python_slave_running = 1;
    }
}

void nebula_python_process_tasks(void) {
    if (__python_slave_running) {
        // Master'dan gelen zaman diliminde (time slice) kısa işleri simüle et
        //printf("[Python Bridge] Tick received from Nebula Master Scheduler...\n");
        printf("[Python Bridge] Processing Python micro-tasks... Done.\n");
        printf("[Python Bridge] Yielding control unconditionally back to Nebula (Master)!\n");
    }
}

void nebula_python_release_handle(int handle_id) {
    if (__python_slave_running) {
        printf("[Python Bridge] GC SYNC: Nebula released reference ownership of Handle #%d.\n", handle_id);
        printf("[Python Bridge] Python GC may now safely collect Handle #%d dynamically.\n", handle_id);
    }
}
