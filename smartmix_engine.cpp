#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsqlite/winsqlite3.h>
#include <string>
#include <vector>
#include <atomic>
#include <thread>
#include <chrono>
#include <mutex>
#include <cmath>
#include <sstream>
#include <fstream>
#include <iomanip>

#include "vdjPlugin8.h"
#include "vdjDsp8.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static void LogDebug(const std::string& msg) {
    static std::mutex logMutex;
    std::lock_guard<std::mutex> lock(logMutex);
    std::ofstream ofs("C:\\Users\\odhis\\AppData\\Local\\VirtualDJ\\smartmix_debug.log", std::ios::app);
    if (ofs.is_open()) {
        auto now = std::chrono::system_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) % 1000;
        time_t timer = std::chrono::system_clock::to_time_t(now);
        struct tm bt;
        localtime_s(&bt, &timer);
        ofs << std::put_time(&bt, "[%H:%M:%S.") << std::setfill('0') << std::setw(3) << ms.count() << "] " << msg << std::endl;
    }
}

class CSmartMixPlugin : public IVdjPluginDsp8 {
public:
    CSmartMixPlugin() 
        : m_running(false), m_smartmixActive(false), m_workerThread(nullptr),
          m_transitioning(false), m_lastOutDeck(-1) {
        LogDebug("CSmartMixPlugin constructor called.");
    }

    ~CSmartMixPlugin() override {
        LogDebug("CSmartMixPlugin destructor called.");
        StopWorker();
    }

    HRESULT VDJ_API OnLoad() override {
        LogDebug("CSmartMixPlugin::OnLoad() called.");
        StartWorker();
        return S_OK;
    }

    HRESULT VDJ_API OnGetPluginInfo(TVdjPluginInfo8 *info) override {
        info->PluginName = "SmartMix";
        info->Author = "SmartMix";
        info->Description = "Exact Cue-Based Transition & Cutoff Engine";
        info->Version = "1.0.0";
        info->Flags = VDJFLAG_PROCESSAFTERSTOP;
        LogDebug("CSmartMixPlugin::OnGetPluginInfo() called.");
        return S_OK;
    }

    ULONG VDJ_API Release() override {
        LogDebug("CSmartMixPlugin::Release() called.");
        StopWorker();
        delete this;
        return S_OK;
    }

    HRESULT VDJ_API OnStart() override {
        m_smartmixActive = true;
        LogDebug("CSmartMixPlugin::OnStart() - SmartMix ACTIVATED.");
        return S_OK;
    }

    HRESULT VDJ_API OnStop() override {
        m_smartmixActive = false;
        LogDebug("CSmartMixPlugin::OnStop() - SmartMix DEACTIVATED.");
        return S_OK;
    }

    HRESULT VDJ_API OnProcessSamples(float *buffer, int nb) override {
        return S_OK;
    }

private:
    void StartWorker() {
        if (m_running) return;
        m_running = true;
        m_workerThread = new std::thread(&CSmartMixPlugin::WorkerLoop, this);
        LogDebug("SmartMix Worker thread spawned.");
    }

    void StopWorker() {
        m_running = false;
        if (m_workerThread) {
            if (m_workerThread->joinable()) {
                m_workerThread->join();
            }
            delete m_workerThread;
            m_workerThread = nullptr;
            LogDebug("SmartMix Worker thread terminated.");
        }
    }

    void WorkerLoop() {
        LogDebug("SmartMix Worker loop started.");
        while (m_running) {
            std::this_thread::sleep_for(std::chrono::milliseconds(25)); // 40 Hz loop

            if (!cb) continue;

            // Check if SmartMix is toggled via skin or internally
            double smRunning = 0.0;
            cb->GetInfo("var '@$smartmix_running'", &smRunning);

            // Also check if user triggered a mix via variable
            double smTriggerNow = 0.0;
            cb->GetInfo("var '@$smartmix_mix_now'", &smTriggerNow);

            // Determine active playing deck
            double play1 = 0.0, play2 = 0.0;
            cb->GetInfo("deck 1 play", &play1);
            cb->GetInfo("deck 2 play", &play2);

            int outDeck = (play1 >= 0.5) ? 1 : ((play2 >= 0.5) ? 2 : 0);
            int inDeck = (outDeck == 1) ? 2 : ((outDeck == 2) ? 1 : 0);

            // Immediate manual mix trigger
            if (smTriggerNow >= 0.5 && outDeck > 0) {
                cb->SendCommand("set '@$smartmix_mix_now' 0");
                ExecuteTransition(outDeck, inDeck);
                continue;
            }

            // If SmartMix is not running, idle
            if (smRunning < 0.5 && !m_smartmixActive) {
                m_transitioning = false;
                continue;
            }

            if (outDeck == 0) continue;

            // Query current playback position in seconds
            double currentPosSec = 0.0;
            std::string qPos = "deck " + std::to_string(outDeck) + " get_time 'sec'";
            cb->GetInfo(qPos.c_str(), &currentPosSec);

            // Query Cutoff Cue (Cue 2) in ms
            double cutoffMs = 0.0;
            std::string qCutoff = "deck " + std::to_string(outDeck) + " cue_pos 2 mseconly";
            cb->GetInfo(qCutoff.c_str(), &cutoffMs);
            double cutoffSec = cutoffMs / 1000.0;

            // Cutoff Cue detection:
            // If track reaches Cue 2 (Cutoff Cue)
            if (cutoffSec > 3.0 && currentPosSec >= (cutoffSec - 0.05)) {
                LogDebug("Cutoff reached on Deck " + std::to_string(outDeck) + " at " + std::to_string(currentPosSec) + "s (Cutoff Cue: " + std::to_string(cutoffSec) + "s). Executing Cutoff Transition to Deck " + std::to_string(inDeck));
                ExecuteCutoffTransition(outDeck, inDeck);
                std::this_thread::sleep_for(std::chrono::milliseconds(1000));
            }
        }
    }

    void ExecuteTransition(int outDeck, int inDeck) {
        // match_bpm sets pitch without moving phase, then goto_cue 1 & play strictly starts at Cue 1
        std::stringstream ss;
        ss << "deck " << inDeck << " match_bpm & "
           << "deck " << inDeck << " goto_cue 1 & "
           << "deck " << inDeck << " play & "
           << "deck " << outDeck << " stop & "
           << "deck " << outDeck << " volume 0% & "
           << "crossfader " << ((inDeck == 2) ? 100 : 0) << "%";
        cb->SendCommand(ss.str().c_str());
        LogDebug("Executed manual transition: " + ss.str());
    }

    void ExecuteCutoffTransition(int outDeck, int inDeck) {
        // match_bpm sets pitch without moving phase, then goto_cue 1 & play strictly starts at Cue 1
        std::stringstream ss;
        ss << "deck " << inDeck << " match_bpm & "
           << "deck " << inDeck << " goto_cue 1 & "
           << "deck " << inDeck << " play & "
           << "deck " << outDeck << " stop & "
           << "deck " << outDeck << " volume 0% & "
           << "crossfader " << ((inDeck == 2) ? 100 : 0) << "%";
        cb->SendCommand(ss.str().c_str());
        LogDebug("Executed cutoff transition: " + ss.str());
    }

    std::atomic<bool> m_running;
    std::atomic<bool> m_smartmixActive;
    std::thread* m_workerThread;
    bool m_transitioning;
    int m_lastOutDeck;
};

// ============================================================================
// DLL Export Entry Point
// ============================================================================

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    if (fdwReason == DLL_PROCESS_ATTACH) {
        LogDebug("SmartMix64.dll: DLL_PROCESS_ATTACH");
    }
    return TRUE;
}

extern "C" __declspec(dllexport) HRESULT __stdcall DllGetClassObject(const GUID &rclsid, const GUID &riid, void** ppObject) {
    LogDebug("DllGetClassObject called.");
    if (rclsid == CLSID_VdjPlugin8 && riid == IID_IVdjPluginDsp8) {
        *ppObject = new CSmartMixPlugin();
        LogDebug("DllGetClassObject returning new CSmartMixPlugin instance.");
        return S_OK;
    }
    LogDebug("DllGetClassObject: requested unsupported interface.");
    return CLASS_E_CLASSNOTAVAILABLE;
}
