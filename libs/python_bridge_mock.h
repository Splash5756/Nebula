#ifndef NEBULA_PYTHON_BRIDGE_MOCK_H
#define NEBULA_PYTHON_BRIDGE_MOCK_H

/**
 * 1. Başlatma ve İzolasyon:
 * Python motorunu ayağa kaldırır gibi davranan, ancak ana thread'i (Main Thread) 
 * kilitlemek yerine "Slave" (Köle) modunda başlatan mock fonksiyon.
 */
void nebula_python_init(void);

/**
 * 2. Master/Slave Olay Döngüsü (Event Loop):
 * Nebula'nın (Master) zamanlayıcısı tarafından periyodik çağrılan, 
 * Python tarafına (Slave) mikro-görevleri işletmesi için kısıtlı zaman veren fonksiyon.
 */
void nebula_python_process_tasks(void);

/**
 * 3. GC (Çöp Toplayıcı) Senkronizasyon Simülasyonu:
 * Nebula tarafından oluşturulmuş bir referansın silindiği ve 
 * Python GC'sine (Çöp toplayıcı) temizlik yetkisinin devredildiği fonksiyon.
 */
void nebula_python_release_handle(int handle_id);

#endif // NEBULA_PYTHON_BRIDGE_MOCK_H
