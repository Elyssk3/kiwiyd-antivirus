//1
#include <iostream>
#include <vector>
#include <string>
#include <filesystem>
#include <ctime>
#include <algorithm>
#include <windows.h>
#include <fstream>
#include <sstream>
#include <unordered_set>
#include <unordered_map>

namespace fs = std::filesystem;

// Структура для хранения информации о файле
struct SuspiciousFile {
    std::string path;
    std::string name;
    std::string extension;
    long long size;
    std::string detectionReason;
};

// Структура для сигнатур в базе данных
struct MalwareSignature {
    std::string name;
    std::string pattern;
    std::string type;
};

// Класс базы данных сигнатур
class MalwareDatabase {
private:
    std::vector<MalwareSignature> signatures;
    std::unordered_set<std::string> knownMaliciousFilenames;
    std::unordered_map<std::string, std::string> suspiciousFileHashes;
    
public:
    MalwareDatabase() {
        loadSignatures();
    }
    
    void loadSignatures() {
        // Известные вредоносные имена файлов
        knownMaliciousFilenames = {
            "virus.exe",
            "malware.exe",
            "ransomware.exe",
            "trojan.exe",
            "backdoor.exe",
            "worm.exe",
            "spyware.exe",
            "adware.exe"
        };
        
        // Простая база сигнатур (примеры опасных расширений и паттернов)
        signatures = {
            {"DoubleExtension", ".*\\.exe\\..*", "executable"},
            {"PSScript", ".*\\.ps1$", "script"},
            {"BatchFile", ".*\\.bat$", "batch"},
            {"CmdFile", ".*\\.cmd$", "command"},
            {"VBScript", ".*\\.vbs$", "script"},
            {"WindowsScript", ".*\\.wsf$", "script"},
            {"CompiledHTML", ".*\\.chm$", "compiled"},
            {"SystemFile", ".*\\.sys$", "system"},
            {"DriverFile", ".*\\.drv$", "driver"}
        };
    }
    
    bool isKnownMalware(const std::string& filename) {
        std::string lower = filename;
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
        return knownMaliciousFilenames.find(lower) != knownMaliciousFilenames.end();
    }
    
    bool matchesSignature(const std::string& filename, std::string& matchedSignature) {
        for (const auto& sig : signatures) {
            // Простая проверка по расширению
            if (filename.find(sig.pattern) != std::string::npos) {
                matchedSignature = sig.name + " (" + sig.type + ")";
                return true;
            }
        }
        return false;
    }
    
    int getTotalSignatures() const {
        return signatures.size() + knownMaliciousFilenames.size();
    }
};

// Глобальная переменная базы данных
MalwareDatabase malwareDB;

// Список подозрительных расширений
const std::vector<std::string> SUSPICIOUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".pif", ".scr", ".vbs", ".js", ".jar",
    ".zip", ".rar", ".7z", ".dll", ".sys", ".drv", ".bin", ".app", ".pkg",
    ".dmg", ".deb", ".rpm", ".sh", ".bash", ".py"
};

// Получить текущее время в формате строки
std::string getCurrentTime() {
    time_t now = time(0);
    struct tm timeinfo;
    localtime_s(&timeinfo, &now);
    
    char buffer[20];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &timeinfo);
    return std::string(buffer);
}

// Получить расширение файла
std::string getFileExtension(const std::string& filename) {
    size_t lastdot = filename.find_last_of(".");
    if (lastdot == std::string::npos) return "";
    
    std::string ext = filename.substr(lastdot);
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
    return ext;
}

// Проверить, является ли расширение подозрительным
bool isSuspiciousExtension(const std::string& extension) {
    return std::find(SUSPICIOUS_EXTENSIONS.begin(), SUSPICIOUS_EXTENSIONS.end(), extension) != SUSPICIOUS_EXTENSIONS.end();
}

// Сканировать директорию на подозрительные файлы
std::vector<SuspiciousFile> scanDirectory(const std::string& startPath, int maxDepth = 3) {
    std::vector<SuspiciousFile> results;
    
    if (!fs::exists(startPath)) {
        return results;
    }
    
    try {
        for (const auto& entry : fs::recursive_directory_iterator(startPath)) {
            try {
                // Ограничить глубину сканирования
                std::string relPath = fs::relative(entry.path(), startPath).string();
                int depth = std::count(relPath.begin(), relPath.end(), '\\');
                
                if (depth >= maxDepth) continue;
                
                if (fs::is_regular_file(entry)) {
                    std::string filename = entry.path().filename().string();
                    std::string extension = getFileExtension(filename);
                    
                    // Проверить по базе данных
                    std::string detectionReason = "";
                    
                    // Проверить на известные вредоносные файлы
                    if (malwareDB.isKnownMalware(filename)) {
                        detectionReason = "Known malware signature";
                    }
                    // Проверить по сигнатурам
                    else if (malwareDB.matchesSignature(filename, detectionReason)) {
                        // detectionReason уже установлена
                    }
                    // Проверить по расширению
                    else if (isSuspiciousExtension(extension)) {
                        detectionReason = "Suspicious extension: " + extension;
                    }
                    
                    if (!detectionReason.empty()) {
                        SuspiciousFile file;
                        file.path = entry.path().string();
                        file.name = filename;
                        file.extension = extension;
                        file.size = fs::file_size(entry.path());
                        file.detectionReason = detectionReason;
                        
                        results.push_back(file);
                    }
                }
            } catch (const std::exception& e) {
                continue;
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "Scan error: " << e.what() << std::endl;
    }
    
    return results;
}

// Основная функция сканирования - вызывается из Python
extern "C" __declspec(dllexport) const char* scanSystem() {
    std::vector<SuspiciousFile> allSuspiciousFiles;
    
   std::string userProfile;
const char* env = std::getenv("USERPROFILE");
if (env) {
    userProfile = env;
}
    
    if (!userProfile.empty()) {
        // Сканировать Downloads
        std::string downloadsPath = std::string(userProfile) + "\\Downloads";
        auto files = scanDirectory(downloadsPath);
        allSuspiciousFiles.insert(allSuspiciousFiles.end(), files.begin(), files.end());
        
        // Сканировать Temp
        std::string tempPath = std::string(userProfile) + "\\AppData\\Local\\Temp";
        if (fs::exists(tempPath)) {
            files = scanDirectory(tempPath);
            allSuspiciousFiles.insert(allSuspiciousFiles.end(), files.begin(), files.end());
        }
        
        // Сканировать Documents
        std::string docsPath = std::string(userProfile) + "\\Documents";
        if (fs::exists(docsPath)) {
            files = scanDirectory(docsPath);
            allSuspiciousFiles.insert(allSuspiciousFiles.end(), files.begin(), files.end());
        }
    }
    
    // Формировать JSON ответ вручную (без зависимостей)
    static std::string result;
    result = "{";
    result += "\"status\":\"completed\",";
    result += "\"timestamp\":\"" + getCurrentTime() + "\",";
    result += "\"database_signatures\":" + std::to_string(malwareDB.getTotalSignatures()) + ",";
    result += "\"total_suspicious\":" + std::to_string(allSuspiciousFiles.size()) + ",";
    result += "\"files\":[";
    
    for (size_t i = 0; i < allSuspiciousFiles.size(); ++i) {
        const auto& file = allSuspiciousFiles[i];
        result += "{";
        result += "\"path\":\"" + file.path + "\",";
        result += "\"name\":\"" + file.name + "\",";
        result += "\"extension\":\"" + file.extension + "\",";
        result += "\"size\":" + std::to_string(file.size) + ",";
        result += "\"reason\":\"" + file.detectionReason + "\"";
        result += "}";
        
        if (i < allSuspiciousFiles.size() - 1) {
            result += ",";
        }
    }
    
    result += "]}";
    
    return result.c_str();
}

// Для консольного тестирования
int main() {
    std::cout << scanSystem() << std::endl;
    return 0;
}
