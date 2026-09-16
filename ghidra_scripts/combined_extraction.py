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

from pathlib import Path
from ghidra.program.model.symbol import SymbolType
from ghidra.program.model.lang import OperandType

from ghidrassist import AnalysisDB
from ghidrassist.graphrag import BinaryKnowledgeGraph
from ghidrassist.graphrag.nodes import KnowledgeNode, NodeType, EdgeType

# NOTE: the decompilation is in C, meaning there are not classes in the traditional sense, 
# so functions are only defined in DLLs or Namespaces

# ======================= symbol extraction helper methods =======================

# returns the string of the type of operand the current operand type is
# (since operand type is an int that represents what type it is)
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

# returns the string version of the symbol type when given the symbol
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

# gets all the instructions from the given function
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

# function to get all the namespaces of the program
# starts with the global namespace, then recursively traverses through the child namespaces
# and adds any symbol of type namespace it comes across
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


# ======================= knowledge node extraction helper methods =======================

# will add the given property to the dictionary if that property exists in the getter method
def add_property(node_dict, key, value):
    if value is not None:
        node_dict[key] = value
    return node_dict

# will add the given list property to dictionary if the list exists
def add_list_property(node_dict, key, value):
    if value:
        # the list returned by the getter is not json serializable,
        # so the list method must be used to get it in the correct format
        value_list = list(value)
        node_dict[key] = value_list
    return node_dict

# # ======================= symbol extraction method =======================
def symbol_extraction(dir_name):
    script_dir = Path(getSourceFile().getAbsolutePath()).parent
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


# ======================= knowledge node extraction method =======================
def knowledge_extraction(dir_name):
    # nested class, imported off the outer class
    GraphEdge = BinaryKnowledgeGraph.GraphEdge

    program_hash = currentProgram.getExecutableSHA256()

    # get the existing "knowledge graph" from the db
    db = AnalysisDB()
    graph = db.getKnowledgeGraph(program_hash)

    # Get all the nodes for the current executable
    all_nodes = []
    for node_type in NodeType.values():
        all_nodes.extend(graph.getNodesByType(node_type))

    node_ids = [n.getId() for n in all_nodes]
    nodes_by_id = {n.getId(): n for n in all_nodes}

    print("Total nodes: {}".format(len(all_nodes)))


    # All edges in one batched query, keyed off every node ID as a source
    all_edges = graph.getEdgesForNodes(node_ids)
    print("Total edges: {}".format(len(all_edges)))

    # break out the knowledge nodes into 4 categories based on type
    binary_list = []
    func_list = []
    ext_list = []
    module_list = []

    # will add the given property to the dictionary if that property exists in the getter method
    def add_property(node_dict, key, value):
        if value is not None:
            node_dict[key] = value
        return node_dict

    # will add the given list property to dictionary if the list exists
    def add_list_property(node_dict, key, value):
        if value:
            # the list returned by the getter is not json serializable,
            # so the list method must be used to get it in the correct format
            value_list = list(value)
            node_dict[key] = value_list
        return node_dict


    # Iterate through each node, add all the necessary data about it, then put it in its respective list
    for node in all_nodes:
        # create new dictionary for node
        new_node = {"name": node.getName(), "id": node.getId()}
        # get all the data properties for the nodes, adding them only if the getter methods for them return non null or empty
        if (node.getAddress() is not None):
            # if the node has an address, put it in the same hex format Ghidra uses
            add_property(new_node, "address", "{:08x}".format(node.getAddress()))
        add_property(new_node, "binaryID", node.getBinaryId())
        add_property(new_node, "rawContent", node.getRawContent())
        add_property(new_node, "signature", node.getSignature())
        add_property(new_node, "decompiledCode", node.getDecompiledCode())
        add_property(new_node, "disassembly", node.getDisassembly())
        add_property(new_node, "llmSummary", node.getLlmSummary())
        add_property(new_node, "summaryConfidence", node.getConfidence())
        add_list_property(new_node, "vectorEmbeddings", node.getEmbedding())
        add_list_property(new_node, "securityFlags", node.getSecurityFlags())
        add_property(new_node, "analysisDepth", node.getAnalysisDepth())
        add_property(new_node, "createdAt", str(node.getCreatedAt()))
        add_property(new_node, "updatedAt", str(node.getUpdatedAt()))
        add_property(new_node, "isStale", node.isStale())
        add_property(new_node, "isUserEdited", node.isUserEdited())
        add_list_property(new_node, "networkAPIs", node.getNetworkAPIs())
        add_list_property(new_node, "fileIOAPIs", node.getFileIOAPIs())
        add_list_property(new_node, "ipAddresses", node.getIPAddresses())
        add_list_property(new_node, "URLs", node.getURLs())
        add_list_property(new_node, "filePaths", node.getFilePaths())
        add_list_property(new_node, "domains", node.getDomains())
        add_list_property(new_node, "registryKeys", node.getRegistryKeys())
        add_property(new_node, "category", node.getCategory())
        add_property(new_node, "activityProfile", node.getActivityProfile())
        add_property(new_node, "riskLevel", node.getRiskLevel())
        
        # dict for all the edges of the current node. The key is the target node id, the value is the type of edge
        # this is to allow for multiple edges of the same type for a node
        edge_dict = {}
        
        outgoing = [e for e in all_edges if e.getSourceId() == node.getId()]
        for edge in outgoing:
            target_node = nodes_by_id.get(edge.getTargetId())
            edge_type = edge.getType()  # EdgeType enum
            # if the target node exists, use that name
            if target_node:
                edge_dict.update({str(target_node.getName()): str(edge_type)})
            # if not, get the id from the edge
            else:
                # if there is a name associated with that id, use that
                target_node = graph.getNode(str(edge.getTargetId()))
                node_name = target_node.getName() if target_node is not None else None
                # use the node name if it exists
                if node_name is not None:
                    # print("name for node found!")
                    edge_dict.update({str(node_name): str(edge_type)})
                # if it doesn't exist, look to see if it is a module/community node
                elif edge_type == EdgeType.BELONGS_TO_COMMUNITY or edge_type == EdgeType.SIBLING:
                    # print("community type edge found")
                    # look through community objects (separate from knowledge nodes)
                    community = graph.getCommunity(str(edge.getTargetId()))
                    # if that community exists, add its name
                    if community is not None:
                        edge_dict.update({str(community.getName()): str(edge_type)})
                    # if not just use the id
                    else:
                        edge_dict.update({str(edge.getTargetId()): str(edge_type)})
                # if the community doesn't exist, then just default to using the id
                else:
                    # print("name for node not found...")
                    edge_dict.update({str(edge.getTargetId()): str(edge_type)})
            
            # print statement for testing 
            # print("{} (id of {})  --[{}]-->  {}".format(
            #     node.getDisplayLabel(),
            #     node.getId(),
            #     edge_type.getDisplayName(),
            #     target_node.getDisplayLabel() if target_node else edge.getTargetId(),
            # ))
            
        new_node.update({"edges": edge_dict})
        # then add the new node to whichever list it belongs in (based on the type of node)
        if (str(node.getType()) == "FUNCTION"):
            func_list.append(new_node)
        elif (str(node.getType()) == "EXTERNAL"):
            ext_list.append(new_node)
        elif (str(node.getType()) == "BINARY"):
            binary_list.append(new_node)
        elif (str(node.getType()) == "MODULE"):
            module_list.append(new_node)
        else:
            print("ERROR: found a node not expected:", node.getDisplayLabel(), "type:", node.getType())

    print("Total functions: {}".format(len(func_list)))

    # get the directory for where the json files will be stored, based on the name the user gives from the input earlier
    script_dir_str = str(Path(getSourceFile().getAbsolutePath()).parent)
    data_dir = script_dir_str + "/" + dir_name

    # get the path for that directory
    directory = Path(data_dir)

    # create the directory if it doesn't already exist
    directory.mkdir(parents=True, exist_ok=True)

    # then make the json files for each node type
    with open(data_dir + "/binaries.json", "w") as f:
        json.dump(binary_list, f, indent=2)
        
    with open(data_dir + "/function-node.json", "w") as f:
        json.dump(func_list, f, indent=2)
        
    with open(data_dir + "/externals.json", "w") as f:
        json.dump(ext_list, f, indent=2)
        
    with open(data_dir + "/modules.json", "w") as f:
        json.dump(module_list, f, indent=2)


def main():
    # new_dir_name = askString("Input Required", "Please enter name to create new directory to store knowledge node information: ", "default_json_output")
    _handoff = Path(__file__).resolve().parent / ".kg_output_dir"
    if _handoff.exists():
        new_dir_name = _handoff.read_text().strip()
    else:
        new_dir_name = askString("Input Required", "Please enter name to create new directory to store knowledge node information: ", "default_json_output")
    symbol_extraction(new_dir_name)
    knowledge_extraction(new_dir_name)
    

if __name__ == "__main__":
    main()