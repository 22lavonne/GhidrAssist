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

# new_dir_name = input("Enter a name for a new directory where the node data will go")
# dir_path = Path(new_dir_name)
new_dir_name = askString("Input Required", "Please enter name to create new directory to store knowledge node information: ")
# new_dir_path = Path(new_dir_name)

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

# get the directory for where the json files will be stored, based on the name the user gives from the input earlier
script_dir_str = str(Path(getSourceFile().getAbsolutePath()).parent)
data_dir = script_dir_str + "/" + new_dir_name

# get the path for that directory
directory = Path(data_dir)

# create the directory if it doesn't already exist
directory.mkdir(parents=True, exist_ok=True)

# then make the json files for each node type
with open(data_dir + "/binaries.json", "w") as f:
    json.dump(binary_list, f, indent=2)
    
with open(data_dir + "/functions.json", "w") as f:
    json.dump(func_list, f, indent=2)
    
with open(data_dir + "/externals.json", "w") as f:
    json.dump(ext_list, f, indent=2)
    
with open(data_dir + "/modules.json", "w") as f:
    json.dump(module_list, f, indent=2)