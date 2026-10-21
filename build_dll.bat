call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d "c:\Users\odhis\Downloads\SmartMix"
cl.exe /LD /O2 /EHsc /MD /DWIN32_LEAN_AND_MEAN smartmix_engine.cpp /link /EXPORT:DllGetClassObject /OUT:SmartMix64.dll winsqlite3.lib
