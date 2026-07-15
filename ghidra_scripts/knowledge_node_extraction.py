#Extracts the data needed from knowledge nodes
#@author Emily Miller
#@category GhidrAssist
#@keybinding 
#@menupath 
#@toolbar 
#@runtime PyGhidra


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

# 2. All edges in one batched query, keyed off every node ID as a source
all_edges = graph.getEdgesForNodes(node_ids)
print("Total edges: {}".format(len(all_edges)))

# break out the knowledge nodes into 4 categories based on type
binary_list = []
func_list = []
ext_list = []
module_list = []

# TODO: modify this to include all the properties needed for knowledge nodes
# Iterate through each node, add all the necessary data about it, then put it in its respective list
for node in all_nodes:
    # create new dictionary for node
    print(node.getDisplayLabel(), node.getType(), node.getId())
    new_node = {"name": node.getName(), "id": node.getId()}
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
            edge_dict.update({str(target_node): str(edge_type)})
        # if not, get the id from the edge
        else:
            edge_dict.update(edge.getTargetId())
            
        print("{}  --[{}]-->  {}".format(
            node.getDisplayLabel(),
            edge_type.getDisplayName(),
            target_node.getDisplayLabel() if target_node else edge.getTargetId(),
        ))
        
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