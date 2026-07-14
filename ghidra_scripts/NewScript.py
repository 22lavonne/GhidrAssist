#TODO write a description for this script
#@author 
#@category GhidrAssist
#@keybinding 
#@menupath 
#@toolbar 
#@runtime PyGhidra


#TODO Add User Code Here

import ghidra
from ghidra.program.model.listing import Program

def main():
    # Fetch the current open program in Ghidra
    # 'currentProgram' is globally injected by Ghidra when running scripts
    program = currentProgram 
    
    if program is not None:
        print(f"Success! Connected to program: {program.getName()}")
        print(f"Executable Path: {program.getExecutablePath()}")
        print(f"Min Address: {program.getMinAddress()}")
    else:
        print("PyGhidra module loaded successfully, but no active program was found.")

if __name__ == "__main__":
    main()
