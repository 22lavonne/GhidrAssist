# modified code from rdflib-starter.py from: https://github.com/kastle-lab/kastle-drawbridge/blob/master/resources/rdflib-starter.py
# rdflib documentation: https://rdflib.readthedocs.io/en/stable/

# expected to run symbol materialization before this one 
# since this file parses from the resulting KG from the symbol materialization


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
#TODO: fix depends on and related to so they better fit the schema
## Structural Properties
CONTAINS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/contains")
CALLS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/calls")
INFERRED_CALLS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/inferredCalls")
REFERENCES = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/references")
INHERITS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/inherits")
## Semantic Edges
SIMILAR_PURPOSE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/similarPurpose")
DEPENDS_ON = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/dependsOn")
RELATED_TO = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/relatedTo")
## Security Edges
VULNERABLE_VIA = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/vulnerableVia")
TAINT_FLOWS_TO = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/taintFlowsTo")
CALLS_VULNERABLE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/callsVulnerable")
NETWORK_SEND = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/networkSend")
## Community Edges 
BELONGS_TO_COMMUNITY = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/belongsToCommunity")
SIBLING = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/sibling")

## other
AT_ADDRESS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/atAddress")



# Data properties 
# Metadata properties
CREATED_AT = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/createdAt")
UPDATED_AT = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/updatedAt")
USER_EDITED = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/userEdited")
HAS_ID = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasID")
# HAS_ADDRESS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasAddress")
HAS_BINARY_ID = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasBinaryID")
HAS_NAME = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasName")
HAS_ANALYSIS_DEPTH = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasAnalysisDepth")
IS_STALE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/isStale")

# content properties
HAS_LLM_SUMMARY = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasLLMSummary")
HAS_SUMMARY_CONFIDENCE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasSummaryConfidence")
HAS_RAW_CONTENT = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasRawContent")
HAS_DECOMPILED_CODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasDecompiledCode")
HAS_DISASSEMBLY = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasDisassembly")
HAS_SIGNATURE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasSignature")
HAS_VECTOR_EMBEDDING = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasVectorEmbedding")


# reverse engineering properties
HAS_RISK_LEVEL = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasRiskLevel")
HAS_ACTIVITY_PROFILE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasActivityProfile")
HAS_CATEGORY = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasCategory")
HAS_SECURITY_FLAG = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasSecurityFlag")
HAS_REGISTRY_KEY = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasRegistryKey")
HAS_NETWORK_API = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasNetworkAPI")
HAS_DOMAIN = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasDomain")
HAS_FILE_IO_API = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasFileIOAPI")
HAS_FILE_PATH = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasFilePath")
HAS_URL = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasURL")
HAS_IP_ADDRESS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasIPAddress")


# classes
# TODO: add classes for content and metadata (maybe)
FUNCTION_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/FunctionNode")
EXTERNAL_FUNCTION_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/ExternalFunctionNode")
BINARY_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/BinaryNode")
MODULE_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/ModuleNode")
# add objects for metadata and content here


edge_dict = {
    "CONTAINS": CONTAINS,
    "CALLS" : CALLS,
    "INFERRED_CALLS": INFERRED_CALLS,
    "REFERENCES": REFERENCES,
    "INHERITS": INHERITS,
    
    "SIMILAR_PURPOSE": SIMILAR_PURPOSE,
    "DEPENDS_ON": DEPENDS_ON,
    "RELATED_TO": RELATED_TO,
    
    "VULNERABLE_VIA": VULNERABLE_VIA,
    "TAINT_FLOWS_TO": TAINT_FLOWS_TO,
    "CALLS_VULNERABLE": CALLS_VULNERABLE,
    "NETWORK_SEND": NETWORK_SEND,
    
    "BELONGS_TO_COMMUNITY": BELONGS_TO_COMMUNITY,
    "SIBLING": SIBLING
    }

property_dict = {
    "createdAt": CREATED_AT,
    "updatedAt": UPDATED_AT,
    "isUserEdited": USER_EDITED,
    "id": HAS_ID,
    "address": AT_ADDRESS,
    "binaryID": HAS_BINARY_ID,
    "name": HAS_NAME,
    "analysisDepth": HAS_ANALYSIS_DEPTH,
    "isStale": IS_STALE,
     
    "llmSummary": HAS_LLM_SUMMARY,
    "summaryConfidence": HAS_SUMMARY_CONFIDENCE,
    "rawContent": HAS_RAW_CONTENT, 
    "decompiledCode": HAS_DECOMPILED_CODE, 
    "disassembly": HAS_DISASSEMBLY, 
    "signature": HAS_SIGNATURE,
    #TODO: change the list properties in this dict if needed
    "vectorEmbeddings": HAS_VECTOR_EMBEDDING,
    
    "riskLevel": HAS_RISK_LEVEL,
    "activityProfile": HAS_ACTIVITY_PROFILE, 
    "category": HAS_CATEGORY,
    "securityFlags": HAS_SECURITY_FLAG,
    "registryKeys": HAS_REGISTRY_KEY, 
    "networkAPIs": HAS_NETWORK_API,
    "domains": HAS_DOMAIN,
    "fileIOAPIs": HAS_FILE_IO_API,
    "filePaths": HAS_FILE_PATH,
    "URLs": HAS_URL,
    "IPAddresses": HAS_IP_ADDRESS,
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
if not dir_path.is_dir():
    print("Directory does not exist. Exiting...")
    exit()
    

script_dir = str(Path(__file__).resolve().parent)


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

# use this to just initialize graph from base ontology
# ontology_path = "../ontology/combined-ontology.ttl"
# with open(ontology_path, "r") as f:
#     graph.parse(f, format="turtle")

# using this instead to initialize kg based on resulting kg from the symbol materialization script
ontology_path = dir_name + "/symbol-output.ttl"
try:
    with open(ontology_path, "r") as f:
        graph.parse(f, format="turtle")
    print("Directory exists, generating knowledge graph from the files in that directory...")
except FileNotFoundError as e:
    print("Error: `symbol-output.ttl not found in that directory. Run `symbol_rdflib_materialization.py` first. Exiting...")
    exit()
except Exception as e:
    print("Error: an unknown exception occurred:", e, "Exiting...")
    exit()

# TODO: change both materialization files to have nodes named by id instead of name if necessary
def materialize_knowledge_node(node, node_type):
    
    # add the node object to the KG
    node_obj = pfs["mkg"][quote_for_turtle(node["name"])]
    if node_type in class_dict:
        graph.add( (node_obj, a, class_dict[node_type]))

    # based on key since the key has the type of property
    for key, value in node.items():
        if key == "edges":
            continue
        # if the current key is address, then add it as an address object/node
        elif key == "address":
            addr_obj = pfs["mkg"][quote_for_turtle(str(value))]
            graph.add( (node_obj, AT_ADDRESS, addr_obj))
            
        elif (key in property_dict):
            # if the current value is a list, then iterate through the list and add all elements of that list to the given node
            if (isinstance(value, list)):
                print("do list stuff here")
                for item in value:
                    # item_obj = pfs["mkg"][quote_for_turtle(str(item))]
                    item_obj = Literal(str(item))
                    graph.add( (node_obj, property_dict[key], item_obj))
            # if it isn't a list then just add the one property to the node here
            else:
                # value_obj = pfs["mkg"][quote_for_turtle(str(value))]
                value_obj = Literal(str(value))
                graph.add( (node_obj, property_dict[key], value_obj))
        else:
            print("Error: the following property type was not found:", key)
    
    
    # add the edge relationships with other nodes
    # based on value since the value has the type of edge
    for key, value in node["edges"].items():
        if (value in edge_dict):
            key_obj = pfs["mkg"][quote_for_turtle(str(key))]
            graph.add( (node_obj, edge_dict[value], key_obj))
        else:
            print("Error: the following edge type was not found:", value)
    
    
# Then add the triples for all 4 kinds of knowledge nodes
for function in func_list:
    materialize_knowledge_node(function, "FUNCTION")
        
        
for external in ext_list:
    materialize_knowledge_node(external, "EXTERNAL")
    

for module in module_list:
    materialize_knowledge_node(module, "MODULE")

for binary in binary_list:
    materialize_knowledge_node(binary, "BINARY")
    

output_file = dir_name + "/combined-output.ttl"
temp = graph.serialize(format="turtle", encoding="utf-8", destination=output_file)
print("Finished materializing. Exiting...")