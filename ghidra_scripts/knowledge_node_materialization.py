# modified code from rdflib-starter.py from: https://github.com/kastle-lab/kastle-drawbridge/blob/master/resources/rdflib-starter.py
# rdflib documentation: https://rdflib.readthedocs.io/en/stable/


import json
from pathlib import Path
from urllib.parse import quote


##### Graph stuff
import rdflib
from rdflib import URIRef, Graph, Namespace, Literal
from rdflib import OWL, RDF, RDFS, XSD, TIME

def load_nodes(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)
    

def quote_for_turtle(obj_string):
    quoted_string = quote(obj_string)
    return_string = quoted_string.replace('%', '_')
    return_string = return_string.replace('.', '_')
    return return_string

# Prefixes
pfs = {
"mkg": Namespace("https://mkg.com/data#"),
"ont": Namespace("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology"),
"rdf": RDF,
"rdfs": RDFS,
"xsd": XSD,
"owl": OWL,
"time": TIME
}

# Object properties
# TODO: add rest of object relations here
CALLS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/calls")
INFERRED_CALLS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/inferredCalls")
VULNERABLE_VIA = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/vulnerableVia")
TAINT_FLOWS_TO = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/taintFlowsTo")
CONTAINS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/contains")


# Data properties 
# TODO: fill out this section
BELONGS_TO_COMMUNITY = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/belongsToCommunity")
HAS_NAME = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasName")


# classes
FUNCTION_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/FunctionNode")
EXTERNAL_FUNCTION_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/ExternalFunctionNode")
BINARY_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/BinaryNode")
MODULE_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/ModuleNode")
# add objects for metadata and content here


edge_dict = {
    "CALLS" : CALLS,
    "INFERRED_CALLS": INFERRED_CALLS,
    "VULNERABLE_VIA": VULNERABLE_VIA,
    "TAINT_FLOWS_TO": TAINT_FLOWS_TO,
    "CONTAINS": CONTAINS,
    "BELONGS_TO_COMMUNITY": BELONGS_TO_COMMUNITY
    }

class_dict = {
    "FUNCTION": FUNCTION_NODE,
    "EXTERNAL": EXTERNAL_FUNCTION_NODE,
    "MODULE": MODULE_NODE,
    "BINARY": BINARY_NODE
    }


# Initialization shortcut
def init_kg(prefixes=pfs):
    kg = Graph()
    for prefix in pfs:
        kg.bind(prefix, pfs[prefix])
    return kg


dir_name = input("What directory do you want to make a knowledge graph from? (needs to exist in the ghidra-scripts directory): ")
dir_path = Path(dir_name)
if dir_path.is_dir():
    print("Directory exists, generating knowledge graph from the files in that directory...")
else:
    print("Directory does not exist. Exiting...")
    exit()

script_dir = str(Path(__file__).resolve().parent)

# node_path = script_dir + "/nodes.json"
# print(node_path)
# node_list = load_nodes(node_path)

binary_path = script_dir + "/binaries.json"
binary_list = load_nodes(binary_path)

func_path = script_dir + "/functions.json"
func_list = load_nodes(func_path)

ext_path = script_dir + "/externals.json"
ext_list = load_nodes(ext_path)

module_path = script_dir + "/modules.json"
module_list = load_nodes(module_path)


# rdf:type shortcut
a = pfs["rdf"]["type"]

# Initialize an empty graph
graph = init_kg()

ontology_path = "../ontology/combined-ontology.ttl"
with open(ontology_path, "r") as f:
    graph.parse(f, format="turtle")


# kastle_members = ["Cogan", "Andrea", "Brandon"]
# for x in kastle_members:
#     # Add a specific triple
#     # g.add( (subject_node, predicate_node, object_node) )
#     graph.add( (pfs["ex"][x], a, pfs["ex"]["Person"]) )

def materialize_knowledge_node(node, node_type):
    # add the node object to the KG
    node_obj = pfs["mkg"][quote_for_turtle(node["id"])]
    if node_type in class_dict:
        graph.add( (node_obj, a, class_dict[node_type]))
    
    # add its name to the KG
    node_name = Literal(str(node["name"]))
    graph.add( (node_obj, HAS_NAME, node_name))
    
    # add the properties for the node here
    
    # add the edge relationships with other nodes
    for key, value in node["edges"].items():
        if (value in edge_dict):
            key_obj = pfs["mkg"][quote_for_turtle(str(key))]
            graph.add( (node_obj, edge_dict[value], key_obj))
        else:
            print("Error: the following edge type was not found:", value)
    
    

for function in func_list:
    materialize_knowledge_node(function, "FUNCTION")
        
        
for external in ext_list:
    materialize_knowledge_node(external, "EXTERNAL")
    

# If there are no modules then this will just not enter the loop and no module nodes will be added
for module in module_list:
    materialize_knowledge_node(module, "MODULE")

for binary in binary_list:
    materialize_knowledge_node(binary, "BINARY")
    
    

output_file = dir_name + "/knowledge-output.ttl"
temp = graph.serialize(format="turtle", encoding="utf-8", destination=output_file)
print("Finished materializing. Exiting...")