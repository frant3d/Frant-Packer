# Frant-Packer

**A lightweight, native C++ packing utility with a dedicated desktop interface.**

Frant-Packer was part of a  larger project called: O-Crypt, That has been discared.
Frant-packer focused exclusively on its packing functionality. The project retains the original graphical interface (Written by AI as I have no python experience.), styling, terminal output, command protocol, and process management while removing the Crypter component and its associated references.

The result is a focused, standalone application with two separate C++ backend implementations and a simple Windows build workflow.

---

## Project Preview

<div align="center">
  <img src="title.gif" alt="Frant-Packer — Project Preview" width="720">
  <br>
  <em>Frant-Packer · Original interface, dedicated packing functionality.</em>
</div>

---

## Features

- **Dedicated Packer Interface** — Retains the original Packer tab and its existing controls.
- **Original GUI and Styling** — Preserves the established layout, stylesheet, terminal, and visual design.
- **Native C++ Backends** — Includes two separate implementations of the packing functionality.
- **Process Management** — Retains the GUI's existing backend process handling and command protocol.
- **Windows Build Support** — Uses MinGW-w64 and GNU Make to compile both C++ implementations.
- **Minimal Project Structure** — Keeps the application focused without unnecessary components or additional GUI tabs.

## Project Structure

```text
Frant-Packer/
├── main.py
├── requirements.txt
├── Makefile
├── bckg.gif
├── title.gif
├── README.md
└── src/
    ├── packer.cpp
    ├── packer-rerun.cpp
    ├── packer.exe          # Generated during compilation
    └── packer-rerun.exe    # Generated during compilation
```

### Core Files

-------------------------------------------------------------------------------------------
| File                   | Description                                                    |
|------------------------|----------------------------------------------------------------|
| `main.py`              | Original GUI                                                   |
| `src/packer.cpp`       | First C++ packing implementation.                              |  
| `src/packer-rerun.cpp` | Alternative C++ packing implementation, maintained separately. |
| `src/title.gif`        | Animated project image displayed in this README.               |
| `Makefile`             | Build rules for both C++ backends.                             |
| `requirements.txt`     | Python dependencies required by the GUI.                       |
-------------------------------------------------------------------------------------------
## Requirements

Before building Frant-Packer, ensure the following are installed:

- **Python 3**
- **MinGW-w64 / g++** — A C++ compiler for Windows.
- **GNU Make** — Used to execute the project's build rules.
- **Python dependencies** — Installed through `requirements.txt`.

Ensure that the compiler and Make are available through your system's `PATH`.

## Installation & Build

### 1. Install Python Dependencies

Open PowerShell in the project directory and run:

```powershell
python -m pip install -r requirements.txt
```

### 2. Compile the C++ Backends

Build both implementations using MinGW Make:

```powershell
mingw32-make
```

This produces:

```text
src/packer.exe
src/packer-rerun.exe
```

The two executables are compiled independently from their respective source files.

### 3. Launch Frant-Packer

Start the graphical interface:

```powershell
python main.py
```

The GUI launches `src/packer.exe`, preserving the original application's backend selection and behavior.

> **Note:** `packer-rerun.exe` is built separately. It is not exposed through an additional GUI tab, keeping the original single-Packer interface intact.

## Design Philosophy

Frant-Packer follows a simple principle: **preserve the original application while removing everything outside the project's intended scope.**

The GUI's existing Packer controls, terminal, command protocol, process handling, and stylesheet remain in place. The Crypter tab and its associated process references are removed, and the application is presented as a standalone packing project.

The two C++ implementations remain separate so that each can be compiled and maintained independently.

## Scope

This repository contains the Packer component only. No Crypter functionality is included in this split.

The project is intended to maintain a minimal, understandable structure while keeping the GUI and native backend components separate.

---

<div align="center">

**Frant-Packer**

*Focused. Native. Minimal.*

</div>