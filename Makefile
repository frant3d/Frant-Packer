CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra
SRC_DIR := src

.PHONY: all clean run
all: $(SRC_DIR)/packer.exe $(SRC_DIR)/packer-rerun.exe

$(SRC_DIR)/packer.exe: $(SRC_DIR)/packer.cpp
	$(CXX) $(CXXFLAGS) "$<" -o "$@"

$(SRC_DIR)/packer-rerun.exe: $(SRC_DIR)/packer-rerun.cpp
	$(CXX) $(CXXFLAGS) "$<" -o "$@"

run: all
	python main.py

clean:
	-del /Q $(SRC_DIR)\packer.exe $(SRC_DIR)\packer-rerun.exe 2>NUL || rm -f $(SRC_DIR)/packer.exe $(SRC_DIR)/packer-rerun.exe
