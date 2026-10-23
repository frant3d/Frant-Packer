// Includes necessary to the project
#include <iostream>
#include <string>
#include <windows.h>
#include <fstream>
#include <vector>
#include <cstdint>
#include <cstring>

using namespace std;

// Function prototypes
void setExe(const string& path);
bool PackExe(const string& path);
void setExport(const string& path);
DWORD SizeAlign(DWORD size, DWORD alignment);

// Global variables
string exeTarget;
uint64_t packSize = 0;
string exportTarget;

// Aligns a value to the specified boundary.
DWORD SizeAlign(DWORD size, DWORD alignment) {
    if (alignment == 0) return size;
    if (size % alignment == 0) return size;
    return ((size / alignment) + 1) * alignment;
}

// Sets the selected executable.
void setExe(const string& path) {
    exeTarget = path;

    cout << "Selected EXE: " << exeTarget << endl;
}

// Packs the selected executable.
bool PackExe(const string& path) {

    // Validate the export location.
    if (exportTarget.empty()) {
        cout << "[ERR] EXPORT LOCATION HAS NOT BEEN SPECIFIED..." << endl;
        return false;
    }

    // Get the source file name.
    size_t slash = exeTarget.find_last_of("\\/");

    string fileName = (slash == string::npos) ? exeTarget : exeTarget.substr(slash + 1);

    // Build the destination path.
    string destination = exportTarget;

    if (!destination.empty() && destination.back() != '\\' && destination.back() != '/') {
        destination += '\\';
    }

    destination += fileName;

    // Copy the executable.
    if (!CopyFileA(exeTarget.c_str(), destination.c_str(), FALSE)) {
        cout << "[ERR] COULD NOT COPY EXE..." << endl;
        cout << "[ERR] Windows error: " << GetLastError() << endl;
        return false;
    }

    cout << "[SUCCESS] EXE COPIED TO: " << destination << endl;

    // Validate the source path.
    if (path.empty()) {
        cout << "[ERR] EXE HAS NOT BEEN SPECIFIED..." << endl;
        return false;
    }

    // Validate the requested size.
    if (packSize == 0) {
        cout << "[ERR] PACK SIZE HAS NOT BEEN SPECIFIED..." << endl;
        return false;
    }

    if (packSize > 1024ULL * 1024ULL * 1024ULL) {
        cout << "[ERR] PACK SIZE CANNOT EXCEED 1 GB..." << endl;
        return false;
    }

    // Verify the exported file.
    if (GetFileAttributesA(destination.c_str()) == INVALID_FILE_ATTRIBUTES) {
        cout << "[ERR] FILE DOES NOT EXIST..." << endl;
        return false;
    }

    cout << "Starting Packing bytes To: " << destination << endl;

    cout << "[INFO] Requested pack size: " << packSize << " bytes." << endl;

    // Open the file for binary read/write.
    fstream file(destination, ios::in | ios::out | ios::binary);

    if (!file.is_open()) {
        cerr << "[ERR] COULD NOT OPEN " << destination << endl;
        return false;
    }

    // Read the DOS header.
    IMAGE_DOS_HEADER DOSheader;
    file.read(reinterpret_cast<char*>(&DOSheader), sizeof(IMAGE_DOS_HEADER));

    // Validate the MZ signature.
    if (DOSheader.e_magic != IMAGE_DOS_SIGNATURE) {
        cout << "[ERR] INVALID DOS HEADER (MZ SIGNATURE MISSING)..." << endl;
        return false;
    }

    // Read the PE headers.
    file.seekg(DOSheader.e_lfanew, ios::beg);

    IMAGE_NT_HEADERS NTheaders;
    file.read(reinterpret_cast<char*>(&NTheaders), sizeof(IMAGE_NT_HEADERS));

    // Validate the PE signature.
    if (NTheaders.Signature != IMAGE_NT_SIGNATURE) {
        cout << "[ERR] INVALID PE FILE..." << endl;
        return false;
    }

    // Get the section count.
    int numSections = NTheaders.FileHeader.NumberOfSections;

    if (numSections == 0) {
        cout << "[ERR] NO SECTIONS FOUND IN EXE..." << endl;
        return false;
    }

    // Calculate the section header offset.
    DWORD sectionHeaderOffset = DOSheader.e_lfanew + sizeof(IMAGE_NT_HEADERS);

    // Read the last section header.
    file.seekg(
        sectionHeaderOffset +
        (sizeof(IMAGE_SECTION_HEADER) * (numSections - 1)),
        ios::beg
    );

    IMAGE_SECTION_HEADER lastSection;
    file.read(reinterpret_cast<char*>(&lastSection), sizeof(IMAGE_SECTION_HEADER));

    // Get the current end of the file.
    file.seekg(0, ios::end);

    streamoff targetByteOffset = file.tellg();

    if (targetByteOffset < 0) {
        cout << "[ERR] COULD NOT DETERMINE FILE SIZE..." << endl;
        file.close();
        return false;
    }

    cout << "[SUCCESS] Calculated target byte offset: 0x"
         << hex << targetByteOffset << dec << endl;

    // Start writing at the end of the file.
    file.seekp(targetByteOffset, ios::beg);

    cout << "[SUCCESS] Ready to pack " << packSize << " bytes." << endl;

    // Use a fixed-size write buffer.
    const size_t chunkSize = 64 * 1024;

    vector<uint8_t> packet(chunkSize, 0);

    // Store the requested size in the buffer.
    if (sizeof(packSize) <= chunkSize) {
        memcpy(packet.data(), &packSize, sizeof(packSize));
    }

    // Write exactly the requested number of bytes.
    uint64_t remaining = packSize;

    while (remaining > 0) {

        size_t bytesToWrite =
            (remaining > chunkSize)
                ? chunkSize
                : static_cast<size_t>(remaining);

        file.write(
            reinterpret_cast<const char*>(packet.data()),
            static_cast<streamsize>(bytesToWrite)
        );

        cout << "[DEBUG] packSize = " << packSize << endl;
        cout << "[DEBUG] packet.size() = " << packet.size() << endl;
        cout << "[DEBUG] Writing exactly " << bytesToWrite << " bytes..." << endl;

        if (!file) {
            cout << "[ERR] FAILED TO WRITE PACK DATA..." << endl;
            file.close();
            return false;
        }

        remaining -= bytesToWrite;
    }

    // Finish the file operation.
    file.flush();
    file.close();

    cout << "[SUCCESS] WROTE " << packSize << " To " << destination << endl;

    return true;
}

// Sets the export directory.
void setExport(const string& path) {
    exportTarget = path;

    cout << "Export location: " << exportTarget << endl;
}

int main() {
    string command;

    // Process commands from GUI.py.
    while (getline(cin, command)) {

        if (command.rfind("exe ", 0) == 0) {
            setExe(command.substr(4));
        }

        else if (command.rfind("size ", 0) == 0) {
            try {

                // Parse the requested size.
                packSize = stoull(command.substr(5));

                if (packSize > 1024ULL * 1024ULL * 1024ULL) {
                    cout << "[ERR] Maximum size is 1 GB." << endl;
                    packSize = 0;
                }

                else if (packSize == 0) {
                    cout << "[ERR] Pack size cannot be 0 bytes." << endl;
                    packSize = 0;
                }

                else {
                    cout << "[SUCCESS] Size set to "
                         << packSize
                         << " bytes."
                         << endl;
                }
            }

            catch (...) {
                cout << "[ERR] Invalid size." << endl;
                packSize = 0;
            }
        }

        else if (command == "start") {
            PackExe(exeTarget);
        }

        else if (command == "stop") {
            cout << "C++ backend stopped" << endl;
        }

        else if (command == "exit") {
            break;
        }

        else if (command.rfind("export ", 0) == 0) {
            setExport(command.substr(7));
        }
    }

    return 0;
}
