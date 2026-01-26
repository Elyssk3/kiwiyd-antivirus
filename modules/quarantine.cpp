//1
#include <iostream>
#include <fstream>
#include <string>
#include <filesystem>
#include <ctime>
#include <sstream>
#include <vector>
#include <windows.h>

namespace fs = std::filesystem;

// Получить текущее время в формате строки
std::string getCurrentTime() {
    time_t now = time(0);
    struct tm timeinfo;
    localtime_s(&timeinfo, &now);
    
    char buffer[20];
    strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &timeinfo);
    return std::string(buffer);
}

// Получить временную метку для имени файла
std::string getTimestamp() {
    time_t now = time(0);
    struct tm timeinfo;
    localtime_s(&timeinfo, &now);
    
    char buffer[20];
    strftime(buffer, sizeof(buffer), "%Y%m%d_%H%M%S_", &timeinfo);
    return std::string(buffer);
}

// Получить директорию карантина


static std::string getQuarantineDir() {
    const char* userProfile = std::getenv("USERPROFILE");
    if (userProfile) {
        return std::string(userProfile) + "\\AppData\\Local\\Temp\\.kiwiyd_quarantine";
    }
    return "";
}
// Инициализировать директорию карантина
void initializeQuarantineDir(const std::string& quarantineDir) {
    if (!fs::exists(quarantineDir)) {
        try {
            fs::create_directories(quarantineDir);
        } catch (const std::exception& e) {
            std::cerr << "Error creating quarantine directory: " << e.what() << std::endl;
        }
    }
}

// Функция карантина - вызывается из Python
extern "C" __declspec(dllexport) const char* quarantineFiles(const char* filePaths) {
    std::string quarantineDir = getQuarantineDir();
    initializeQuarantineDir(quarantineDir);
    
    static std::string result;
    result = "{";
    result += "\"status\":\"completed\",";
    result += "\"timestamp\":\"" + getCurrentTime() + "\",";
    result += "\"quarantine_location\":\"" + quarantineDir + "\",";
    
    int successCount = 0;
    int failureCount = 0;
    std::string quarantinedJson = "";
    std::string failedJson = "";
    
    // Парсить входные пути (разделены ;)
    std::istringstream iss(filePaths);
    std::string filePath;
    
    while (std::getline(iss, filePath, ';')) {
        // Удалить пробелы
        filePath.erase(0, filePath.find_first_not_of(" \t\r\n"));
        filePath.erase(filePath.find_last_not_of(" \t\r\n") + 1);
        
        if (filePath.empty()) continue;
        
        try {
            if (!fs::exists(filePath)) {
                if (!failedJson.empty()) failedJson += ",";
                failedJson += "{\"file\":\"" + filePath + "\",\"error\":\"File not found\"}";
                failureCount++;
                continue;
            }
            
            std::string filename = fs::path(filePath).filename().string();
            std::string timestamp = getTimestamp();
            std::string quarantinePath = quarantineDir + "\\" + timestamp + filename;
            
            // Переместить файл в карантин
            fs::rename(filePath, quarantinePath);
            
            if (!quarantinedJson.empty()) quarantinedJson += ",";
            quarantinedJson += "{\"original\":\"" + filePath + "\",\"quarantined\":\"" + quarantinePath + "\"}";
            successCount++;
            
        } catch (const std::exception& e) {
            if (!failedJson.empty()) failedJson += ",";
            failedJson += "{\"file\":\"" + filePath + "\",\"error\":\"" + std::string(e.what()) + "\"}";
            failureCount++;
        }
    }
    
    result += "\"quarantined_count\":" + std::to_string(successCount) + ",";
    result += "\"failed_count\":" + std::to_string(failureCount) + ",";
    result += "\"quarantined_files\":[" + quarantinedJson + "],";
    result += "\"failed_files\":[" + failedJson + "]";
    result += "}";
    
    return result.c_str();
}

// Функция для восстановления из карантина
extern "C" __declspec(dllexport) const char* restoreFromQuarantine(const char* quarantinedFilePath, const char* restorePath) {
    static std::string result;
    result = "{";
    result += "\"status\":\"completed\",";
    result += "\"timestamp\":\"" + getCurrentTime() + "\",";
    
    try {
        if (!fs::exists(quarantinedFilePath)) {
            result += "\"status\":\"error\",";
            result += "\"error\":\"File not found in quarantine\"";
        } else {
            fs::rename(quarantinedFilePath, restorePath);
            result += "\"status\":\"success\",";
            result += "\"original\":\"" + std::string(quarantinedFilePath) + "\",";
            result += "\"restored_to\":\"" + std::string(restorePath) + "\"";
        }
    } catch (const std::exception& e) {
        result += "\"status\":\"error\",";
        result += "\"error\":\"" + std::string(e.what()) + "\"";
    }
    
    result += "}";
    
    return result.c_str();
}

// Функция для получения списка файлов в карантине
extern "C" __declspec(dllexport) const char* getQuarantineList() {
    std::string quarantineDir = getQuarantineDir();
    
    static std::string result;
    result = "{";
    result += "\"status\":\"completed\",";
    result += "\"timestamp\":\"" + getCurrentTime() + "\",";
    result += "\"quarantine_location\":\"" + quarantineDir + "\",";
    result += "\"files\":[";
    
    int fileCount = 0;
    
    if (fs::exists(quarantineDir)) {
        try {
            for (const auto& entry : fs::directory_iterator(quarantineDir)) {
                if (fs::is_regular_file(entry)) {
                    if (fileCount > 0) result += ",";
                    result += "{";
                    result += "\"name\":\"" + entry.path().filename().string() + "\",";
                    result += "\"path\":\"" + entry.path().string() + "\",";
                    result += "\"size\":" + std::to_string(fs::file_size(entry)) + "";
                    result += "}";
                    fileCount++;
                }
            }
        } catch (const std::exception& e) {
            std::cerr << "Error reading quarantine: " << e.what() << std::endl;
        }
    }
    
    result += "]";
    result += "}";
    
    return result.c_str();
}

// Для консольного тестирования
int main() {
    std::cout << "Quarantine List:" << std::endl;
    std::cout << getQuarantineList() << std::endl;
    return 0;
}
