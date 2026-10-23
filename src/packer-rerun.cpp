// Includes necessary to the project
#include <iostream>
#include <string>
#include <windows.h>
#include <fstream>
#include <vector>
#include <cstdint>
#include <cstring> 



using namespace std;

// Function Prototypes
void setExe(const string& path);    // Function that sets the EXE through GUI.py
bool PackExe(const string& path); // Function that Packs the EXE
void setExport(const string& path); // Used to export the EXE
DWORD SizeAlign(DWORD size, DWORD alignment);




// Needed Variables.
string exeTarget;       // Selected EXE path
uint64_t packSize = 0;  // Requested pack size
string exportTarget;    // Selected export directory


// A function that helps to align the offsets accordingly to the PE specs.
DWORD SizeAlign(DWORD size, DWORD alignment) {
    if (alignment == 0) return size; // Avoid division by zero
    if (size % alignment == 0) return size; // Already aligned
    return ((size / alignment) + 1) * alignment; // Align to next boundary

}


// Sets the EXE through
void setExe(const string& path) {
    exeTarget = path;

    cout << "Selected EXE: " << exeTarget << endl;

}


// Function that packs the EXE with X bytes
bool PackExe(const string& path) {

    // Copy the selected EXE to the export directory.
    if (exportTarget.empty()) {
        cout << "[ERR] EXPORT LOCATION HAS NOT BEEN SPECIFIED..." << endl;
        return false;

    }

    size_t slash = exeTarget.find_last_of("\\/"); // Find the filename separator

    string fileName = (slash == string::npos) ? exeTarget : exeTarget.substr(slash + 1);

    string destination = exportTarget; // Build the output path

    if (!destination.empty() && destination.back() != '\\' && destination.back() != '/') {
        destination += '\\';
    }

    destination += fileName;

    // Create the exported copy before modifying it.
    if (!CopyFileA(exeTarget.c_str(), destination.c_str(), FALSE)) {
        cout << "[ERR] COULD NOT COPY EXE..." << endl;
        cout << "[ERR] Windows error: " << GetLastError() << endl;
        return false;

    }

    cout << "[SUCCESS] EXE COPIED TO: " << destination << endl;

    if (path.empty()) {
        cout << "[ERR] EXE HAS NOT BEEN SPECIFIED..." << endl;
        return false;

    }

    if (packSize == 0) {
        cout << "[ERR] PACK SIZE HAS NOT BEEN SPECIFIED..." << endl;
        return false;

    }

    if (packSize > 1024ULL * 1024ULL * 1024ULL) {
        cout << "[ERR] PACK SIZE CANNOT EXCEED 1 GB..." << endl;
        return false;

    }

    // Check that the exported copy exists.
    if (GetFileAttributesA(destination.c_str()) == INVALID_FILE_ATTRIBUTES) {
        cout << "[ERR] FILE DOES NOT EXIST..." << endl;
        return false;

    }

    
    cout << "Starting Packing bytes To: " << destination << endl;

    cout << "[INFO] Requested pack size: " << packSize << " bytes." << endl;
    
    // Opens file in bin R+W
    fstream file(destination, ios::in | ios::out | ios::binary);
    
    if (!file.is_open()) {
        cerr << "[ERR] COULD NOT OPEN " << destination << endl;
        return false;

    }

    // DOS header verification
    IMAGE_DOS_HEADER DOSheader;
    file.read(reinterpret_cast<char*>(&DOSheader), sizeof(IMAGE_DOS_HEADER));

    // Check for the MZ signature.
    if (DOSheader.e_magic != IMAGE_DOS_SIGNATURE) {
        cout << "[ERR] INVALID DOS HEADER (MZ SIGNATURE MISSING)..." << endl;
        return false;

    }
    

    // Jmp and read NT headers (PE signa +  File/Opt headers)
    file.seekg(DOSheader.e_lfanew, ios::beg);
    IMAGE_NT_HEADERS NTheaders;
    file.read(reinterpret_cast<char*>(&NTheaders), sizeof(IMAGE_NT_HEADERS));

    // Check for the PE signature.
    if (NTheaders.Signature != IMAGE_NT_SIGNATURE) {
        cout << "[ERR] INVALID PE FILE..." << endl;
        return false;
        
    }

    // Get number of sections
    int numSections = NTheaders.FileHeader.NumberOfSections;
    if (numSections == 0) {
        cout << "[ERR] NO SECTIONS FOUND IN EXE..." << endl;
        return false;

    }

    // Calculate section headers offset
    DWORD sectionHeaderOffset = DOSheader.e_lfanew + sizeof(IMAGE_NT_HEADERS);

    // Jmp to the last section header
    file.seekg(sectionHeaderOffset + (sizeof(IMAGE_SECTION_HEADER) * (numSections - 1)), ios::beg);
    IMAGE_SECTION_HEADER lastSection;
    file.read(reinterpret_cast<char*>(&lastSection), sizeof(IMAGE_SECTION_HEADER));

    // Move to the actual end of the file.
    // The existing PE data is left unchanged.
    file.clear();
    file.seekp(0, ios::end);

    if (!file) {
        cout << "[ERR] COULD NOT SEEK TO END OF FILE..." << endl;
        file.close();
        return false;
    }

    cout << "[SUCCESS] Ready to pack "<< packSize << " bytes." << endl;

    // Using mem copy, copies said byte sizes into the buffer
    vector<uint8_t> packet(packSize, 0);

    // Store the pack size at the start of the buffer.
    if (sizeof(packSize) <= packSize) {
        memcpy(packet.data(), &packSize, sizeof(packSize));

    }

    cout << "[SUCCESS] WROTE " << packSize << " To " << destination << endl;

    // Write the generated bytes to the end of the exported EXE.
    file.write(reinterpret_cast<const char*>(packet.data()), packet.size());

    if (!file) {
        cout << "[ERR] FAILED TO WRITE PACK DATA..." << endl;
        file.close();
        return false;
    }

    file.close();

    return true;

}


void setExport(const string& path) {
    exportTarget = path; // Store the export directory

    cout << "Export location: " << exportTarget << endl;
}








int main() {
    string command;

    // Read commands continuously from GUI.py.
    while (getline(cin, command)) {
        if (command.rfind("exe ", 0) == 0) {
            setExe(command.substr(4));

        }

        else if (command.rfind("size ", 0) == 0) {
            try {
                // Convert the requested size from text to a number.
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
                    cout << "[SUCCESS] Size set to " << packSize << " bytes." << endl;

                }

            }

            catch (...) {
                // Invalid numeric input.
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
