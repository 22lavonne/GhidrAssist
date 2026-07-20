#Extracts the data needed from knowledge nodes
#@author Emily Miller
#@category GhidrAssist
#@keybinding 
#@menupath 
#@toolbar 
#@runtime PyGhidra

import json
from pathlib import Path


from ghidrassist import AnalysisDB
from ghidrassist.graphrag import BinaryKnowledgeGraph
from ghidrassist.graphrag.nodes import KnowledgeNode, NodeType, EdgeType


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
    

# TODO: modify this to include all the properties needed for knowledge nodes
# Iterate through each node, add all the necessary data about it, then put it in its respective list
for node in all_nodes:
    # create new dictionary for node
    new_node = {"name": node.getName(), "id": node.getId()}
    # get all the data properties for the nodes, adding them only if the getter methods for them return non null or empty
    # new_node["address"] = node.getAddress()
    #TODO: change some of these properties to strings if necessary
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
    # TODO: might need to change this if there are instances where there are multiple edges to the same target node for a source node
    edge_dict = {}
    
    outgoing = [e for e in all_edges if e.getSourceId() == node.getId()]
    for edge in outgoing:
        target_node = nodes_by_id.get(edge.getTargetId())
        edge_type = edge.getType()  # EdgeType enum
        # if the target node exists, use that id
        if target_node:
            edge_dict.update({str(target_node.getId()): str(edge_type)})
        # if not, get the id from the edge
        else:
            edge_dict.update({str(edge.getTargetId()): str(edge_type)})
            
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
        
# for node in node_list:
#     for item in node:
#         print(item)
# # print(node_list)
# put all the list/dictionary data into a json file that will be used later

#TODO: make 4 separate json files to separate the types of knowledge nodes
script_dir_str = str(Path(getSourceFile().getAbsolutePath()).parent)
with open(script_dir_str + "/binaries.json", "w") as f:
    json.dump(binary_list, f, indent=2)
    
with open(script_dir_str + "/functions.json", "w") as f:
    json.dump(func_list, f, indent=2)
    
with open(script_dir_str + "/externals.json", "w") as f:
    json.dump(ext_list, f, indent=2)
    
with open(script_dir_str + "/modules.json", "w") as f:
    json.dump(module_list, f, indent=2)