#@Emily Miller
#@category GhidrAssist
#@keybinding 
#@menupath 
#@toolbar 
#@runtime PyGhidra

import os
import sys
import json
from pathlib import Path

from ghidra.program.model.symbol import SymbolType
from ghidra.program.model.lang import OperandType


def get_operand_type_string(op_type):
    if OperandType.isRegister(op_type):
        return "REGISTER"
    elif OperandType.isImmediate(op_type):
        return "IMMEDIATE"
    elif OperandType.isAddress(op_type):
        return "ADDRESS"
    elif OperandType.isIndirect(op_type) or OperandType.isDataReference(op_type):
        return "MEMORY"
    elif OperandType.isImplicit(op_type):
        return "IMPLICIT"
    elif OperandType.isScalar(op_type):
        return "SCALAR"
    elif OperandType.isDynamic(op_type):
        return "DYNAMIC"
    return "UNKNOWN"


def get_symbol_type_string(symbol):
    if not symbol:
        return ""
    stype = symbol.getSymbolType()
    if stype == SymbolType.FUNCTION:
        return "FUNCTION"
    elif stype in [SymbolType.NAMESPACE, SymbolType.GLOBAL]:
        return "NAMESPACE"
    elif stype == SymbolType.CLASS:
        return "CLASS"
    elif stype == SymbolType.LIBRARY:
        return "DLL"
    elif stype == SymbolType.PARAMETER:
        return "PARAMETER"
    elif stype == SymbolType.LABEL:
        return "LABEL"
    return ""


def extract_references(ref_array):
    references = []
    if not ref_array:
        return references
        
    for ref in ref_array:
        references.append({
            "source": str(ref.getFromAddress()),
            "destination": str(ref.getToAddress()),
            "operand_index": ref.getOperandIndex(),
            "type": str(ref.getReferenceType()),
            "is_primary": ref.isPrimary()
        })
    return references


def extract_instructions_from_function(func):
    instructions = []
    if func is None:
        return instructions
        
    func_entry = func.getAddress()
    func_obj = currentProgram.getFunctionManager().getFunctionAt(func_entry)
    if not func_obj:
        return instructions
        
    body = func_obj.getBody()
    instruction_iterator = currentProgram.getListing().getInstructions(body, True)
    
    for ins in instruction_iterator:
        num_operands = ins.getNumOperands()
        operands = []
        
        for op_index in range(num_operands):
            op_type_str = get_operand_type_string(ins.getOperandType(op_index))
            op_rep = ins.getDefaultOperandRepresentation(op_index)
            
            if num_operands == 1:
                role = "SOURCE_AND_DESTINATION"
            elif op_index == num_operands - 1:
                role = "DESTINATION"
            else:
                role = "SOURCE"
                
            operands.append({
                "index": op_index,
                "representation": op_rep,
                "type": op_type_str,
                "role": role
            })

        instructions.append({
            "min_address": str(ins.getMinAddress()),
            "opcode": ins.getMnemonicString().upper(),
            "in_function": str(func.getName()),
            "num_operands": num_operands,
            "operands": operands
        })
        
    return instructions


def get_all_namespaces(program, monitor):
    symbol_table = program.getSymbolTable()
    global_namespace = program.getGlobalNamespace()
    all_namespaces = []

    def traverse_namespaces(parent_namespace):
        parent_symbol = parent_namespace.getSymbol()
        children_symbols = symbol_table.getChildren(parent_symbol)
        
        for symbol in children_symbols:
            if monitor.isCancelled():
                return 
            if symbol.getSymbolType() in [SymbolType.NAMESPACE, SymbolType.CLASS, SymbolType.LIBRARY, SymbolType.FUNCTION]:
                child_namespace = symbol.getObject()
                if child_namespace.getSymbol().getSymbolType() == SymbolType.NAMESPACE:
                    all_namespaces.append(child_namespace)
                    traverse_namespaces(child_namespace)

    traverse_namespaces(global_namespace)
    return all_namespaces


def main():
    script_dir = Path(getSourceFile().getAbsolutePath()).parent
    dir_name = askString("Name", "Enter new directory name:", "default_json_output")
    new_dir = script_dir / dir_name
    
    try:
        os.mkdir(new_dir)
        print("Directory '{}' created successfully.".format(new_dir))
    except FileExistsError:
        print("Directory '{}' already exists.".format(new_dir))
    except Exception as e:
        print("Error creating directory: {}".format(e))
        return

    # Data collections
    functions = []
    instructions = []
    labels = []
    parameters = []
    local_variables = []
    classes = []
    dlls = []
    namespaces = []

    # 1. Process Symbols (Functions, Labels, Parameters, Local Variables, Instructions)
    symbol_iterator = currentProgram.getSymbolTable().getSymbolIterator()
    for s in symbol_iterator:
        parent_symbol = s.getParentNamespace().getSymbol() if s.getParentNamespace() else None
        refs = extract_references(s.getReferences())
        
        if s.getSymbolType() == SymbolType.FUNCTION:
            func_obj = s.getObject()
            
            # Instructions
            instructions.extend(extract_instructions_from_function(s))
            
            # Called Functions
            called_funcs = func_obj.getCalledFunctions(monitor)
            called_func_names = [f.getName() for f in called_funcs] if called_funcs else []
            
            # Function object
            functions.append({
                "name": s.getName(),
                "address": str(s.getAddress()),
                "return_type": str(func_obj.getReturnType()),
                "return_value": str(func_obj.getReturn()),
                "parent": str(s.getParentNamespace()),
                "parent_type": get_symbol_type_string(parent_symbol),
                "called_functions": called_func_names,
                "references": refs
            })

            # Local Variables
            locals_list = func_obj.getLocalVariables()
            if locals_list:
                for local in locals_list:
                    local_variables.append({
                        "name": local.getName(),
                        "data_type": str(local.getDataType()),
                        "parent": s.getName(),
                        "parent_type": "FUNCTION"
                    })

            # Parameters
            params_list = func_obj.getParameters()
            if params_list:
                for param in params_list:
                    parameters.append({
                        "name": param.getName(),
                        "data_type": str(param.getDataType()),
                        "parent": s.getName(),
                        "parent_type": "FUNCTION"
                    })
        else:
            # Labels (and other generic symbols)
            labels.append({
                "name": s.getName(),
                "address": str(s.getAddress()),
                "parent": str(s.getParentNamespace()),
                "parent_type": get_symbol_type_string(parent_symbol),
                "references": refs
            })

    # 2. Process Classes
    class_iterator = currentProgram.getSymbolTable().getClassNamespaces()
    for c in class_iterator:
        c_symbol = c.getSymbol()
        parent_symbol = c.getParentNamespace().getSymbol() if c.getParentNamespace() else None
        classes.append({
            "name": str(c),
            "address": str(c_symbol.getAddress()),
            "parent": str(c.getParentNamespace()),
            "parent_type": get_symbol_type_string(parent_symbol),
            "references": extract_references(c_symbol.getReferences())
        })

    # 3. Process DLLs (External Libraries)
    ext_manager = currentProgram.getExternalManager()
    for dll_str in ext_manager.getExternalLibraryNames():
        dll_symbol = ext_manager.getExternalLibrary(dll_str).getSymbol()
        parent_symbol = dll_symbol.getParentNamespace().getSymbol() if dll_symbol.getParentNamespace() else None
        dlls.append({
            "name": dll_str,
            "address": str(dll_symbol.getAddress()),
            "parent": str(dll_symbol.getParentNamespace()),
            "parent_type": get_symbol_type_string(parent_symbol),
            "references": extract_references(dll_symbol.getReferences())
        })

    # 4. Process Namespaces
    for ns in get_all_namespaces(currentProgram, monitor):
        ns_symbol = ns.getSymbol()
        parent_symbol = ns.getParentNamespace().getSymbol() if ns.getParentNamespace() else None
        namespaces.append({
            "name": str(ns),
            "address": str(ns_symbol.getAddress()),
            "parent": str(ns.getParentNamespace()),
            "parent_type": get_symbol_type_string(parent_symbol),
            "references": extract_references(ns_symbol.getReferences())
        })

    # Save to individual JSON files
    output_files = {
        "function.json": functions,
        "instruction.json": instructions,
        "label.json": labels,
        "class.json": classes,
        "dll.json": dlls,
        "namespace.json": namespaces,
        "parameter.json": parameters,
        "local_variable.json": local_variables
    }

    for file_name, data in output_files.items():
        output_path = new_dir / file_name
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    print("Successfully exported data to JSON files in: {}".format(new_dir))


if __name__ == "__main__":
    main()