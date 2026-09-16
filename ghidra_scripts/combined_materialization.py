# modified code from rdflib-starter.py from: https://github.com/kastle-lab/kastle-drawbridge/blob/master/resources/rdflib-starter.py
# rdflib documentation: https://rdflib.readthedocs.io/en/stable/

import sys
import json
from pathlib import Path
from urllib.parse import quote

##### Graph stuff
from rdflib import URIRef, Graph, Namespace, Literal
from rdflib import OWL, RDF, RDFS, XSD, TIME

# Prefixes
name_space = "https://kastle-lab.org/"
pfs = {
"mkg": Namespace("https://mkg.com/data#"),
"ont": Namespace("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology"),
"rdf": RDF,
"rdfs": RDFS,
"xsd": XSD,
"owl": OWL,
"time": TIME
}

# helper methods
# Initialization shortcut
def init_kg(prefixes=pfs):
    kg = Graph()
    for prefix in pfs:
        kg.bind(prefix, pfs[prefix])
    return kg
# rdf:type shortcut
a = pfs["rdf"]["type"]

# gets the list of dictionaries from a given path to the json files
def load_nodes(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)
    
# method that removes RDF unfriendly characters from strings
# so they can be added as RDF objects safely.
def quote_for_turtle(obj_string):
    quoted_string = quote(obj_string)
    return_string = quoted_string.replace('%', '_')
    return_string = return_string.replace('.', '_')
    return return_string

def load_json(file_path):
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []

# method to add references triples for multiple kinds of objects (for symbol materialization)
# takes in the object instance URI, the reference object,
# and a boolean for if the current reference is considered primary
def add_reference(object_instance, reference, isPrimary=False):
    # name the reference based on both the source and destination addresses
    ref = pfs["mkg"]["ref_" + quote(str(reference['source'])) + "_to_" + quote(str(reference['destination']))]
    graph.add((ref, a, REFERENCE))
    
    # make a slightly different triple based on if the current reference is primary
    is_primary_ref = isPrimary or reference.get('is_primary', False)
    if is_primary_ref:
        graph.add((object_instance, hasPrimaryReference, ref))
    else:
        graph.add((object_instance, hasReference, ref))
    
    # add other information about reference
    src_add = pfs["mkg"][quote(str(reference['source']))]
    dest_add = pfs["mkg"][quote(str(reference['destination']))]
    op_index = Literal(reference.get('operand_index', reference.get('operandindex')))
    ref_type = Literal(reference['type'])
    
    graph.add((ref, hasSourceAddress, src_add))
    graph.add((ref, hasDestinationAddress, dest_add))
    graph.add((ref, hasOperandIndex, op_index))
    graph.add((ref, hasReferenceType, ref_type))

# function that will create all necessary RDF triples for a given node.
# takes in a node dictionary and a string representing the type of node
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
        elif key == "ipAddresses":
            addr_obj = pfs["mkg"][quote_for_turtle(str(value))]
            graph.add( (node_obj, AT_ADDRESS, addr_obj))
            
        # else if it's a property, add the data property relation
        elif (key in property_dict):
            # if the current value is a list, then iterate through the list and add all elements of that list to the given node
            if (isinstance(value, list)):
                for item in value:
                    item_obj = Literal(str(item))
                    graph.add( (node_obj, property_dict[key], item_obj))
                    
            # if it isn't a list then just add the one property to the node here
            else:
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
    



# ====================== Symbol Properties ======================
# Object Properties
definedIn = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/definedIn")
calls = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/calls")
hasParameter = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasParameter")
passesInto = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/passesInto")
returns = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/returns")
containsInstruction = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/containsInstruction")
atAddress = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/atAddress")
hasSourceAddress = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasSourceAddress")
hasDestinationAddress = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasDestinationAddress")
hasReference = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasReference")
hasPrimaryReference = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasPrimaryReference")
hasSourceOperand = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasSourceOperand")
hasDestinationOperand = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasDestinationOperand")
defines = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/defines")

# Data Properties
hasOperandIndex = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasOperandIndex")
hasReferenceType = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasReferenceType")
hasOpcode = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasOpcode")
hasOperandType = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasOperandType")
hasOperandValue = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasOperandValue")
hasName = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasName")
hasDataType = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasDataType")
hasReturnType = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasReturnType")

# Classes
SYMBOL = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Symbol")
LABEL = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Label")
NAMESPACE_SYMBOL = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/NamespaceSymbol")
STRUCTURAL_NAMESPACE_SYMBOL = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/StructuralNamespaceSymbol")
NAMESPACE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Namespace")
CLASS_ = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Class")
EXTERNAL_FUNCTION_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/ExternalFunctionNode")
FUNCTION_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/FunctionNode")
VARIABLE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Variable")
LOCAL_VARIABLE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/LocalVariable")
PARAMETER = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Parameter")
ADDRESS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Address")
REFERENCE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Reference")
INSTRUCTION = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Instruction")
OPERAND = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/Operand")

# used to map the string version of a symbol name to the URIRef variable for that object
class_dict = {
    "SYMBOL": SYMBOL,
    "LABEL": LABEL,
    "NAMESPACE_SYMBOL": NAMESPACE_SYMBOL,
    "STRUCTURAL_NAMESPACE_SYMBOL": STRUCTURAL_NAMESPACE_SYMBOL,
    "NAMESPACE": NAMESPACE,
    "CLASS_": CLASS_,
    "DLL": EXTERNAL_FUNCTION_NODE,
    "FUNCTION": FUNCTION_NODE,
    "VARIABLE": VARIABLE,
    "LOCAL_VARIABLE": LOCAL_VARIABLE,
    "PARAMETER": PARAMETER,
    "ADDRESS": ADDRESS,
    "REFERENCE": REFERENCE,
    "INSTRUCTION": INSTRUCTION,
    "OPERAND": OPERAND,
}


# ====================== Knowledge Node Properties ======================
# Object properties
## Structural Edges
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
NETWORK_RECV = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/networkRecv")
## Community Edges 
BELONGS_TO_COMMUNITY = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/belongsToCommunity")
SIBLING = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/sibling")

## Other
AT_ADDRESS = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/atAddress")


# Data properties 
# Metadata properties
CREATED_AT = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/createdAt")
UPDATED_AT = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/updatedAt")
USER_EDITED = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/userEdited")
HAS_ID = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/hasID")
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


# Classes (for knowledge nodes)
FUNCTION_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/FunctionNode")
EXTERNAL_FUNCTION_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/ExternalFunctionNode")
BINARY_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/BinaryNode")
MODULE_NODE = URIRef("http://www.semanticweb.org/jaspe/ontologies/2026/0/combined-ontology/ModuleNode")

# dictionary containing all the edges, used for easier traversal for data to turn into triples
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
    "NETWORK_RECV": NETWORK_RECV,
    "BELONGS_TO_COMMUNITY": BELONGS_TO_COMMUNITY,
    "SIBLING": SIBLING
    }

# dictionary containing all data properties
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

# dictionary with all types of classes (knowledge nodes)
class_dict = {
    "FUNCTION": FUNCTION_NODE,
    "EXTERNAL": EXTERNAL_FUNCTION_NODE,
    "MODULE": MODULE_NODE,
    "BINARY": BINARY_NODE
    }

    
# Initialize an empty graph
graph = init_kg()

# parse the ontology file
# ontology = "ontology/combined-ontology.ttl"
script_dir = Path(__file__).resolve().parent
ontology_path = script_dir.parent / "ontology" / "combined-ontology.ttl"
if not ontology_path.is_file():
    print("Ontology not found at: %s" % ontology_path)
    print("Expected 'ontology/combined-ontology.ttl' one level above the scripts directory.")
    sys.exit(1)
with open(ontology_path, "r", encoding="utf-8") as f:
    graph.parse(f, format="turtle")

# Directory name comes from argv when launched by the GhidrAssist "Generate KG"
# button; fall back to prompting when run by hand. It is resolved against this
# script's own directory rather than the current working directory, which is not
# reliable when the process is started by Ghidra (and is not usable at all when
# the scripts live on a UNC/WSL path).
if len(sys.argv) > 1:
    dir_name = sys.argv[1].strip()
else:
    dir_name = input("What directory do you want to make a knowledge graph from? (needs to exist in the ghidra-scripts directory): ").strip()

dir_path = script_dir / dir_name
if dir_path.is_dir():
    print("Directory exists, generating knowledge graph from the files in that directory...")
else:
    # Exit non-zero so the caller can distinguish this from a successful run.
    print("Directory does not exist: %s. Exiting..." % dir_path)
    sys.exit(1)

# ===================== symbol materialization =====================

# Data files, and lists of dictionaries containing the data based on the directory given
parameters_list = load_json(dir_path / "parameter.json")
local_var_list = load_json(dir_path / "local_variable.json")
function_list = load_json(dir_path / "function.json")
label_list = load_json(dir_path / "label.json")
class_list = load_json(dir_path / "class.json")
dll_list = load_json(dir_path / "dll.json")
namespace_list = load_json(dir_path / "namespace.json")
instruction_list = load_json(dir_path / "instruction.json")

# Local variable format example: 
# {'var': 'local_8', 'datatype': 'undefined4', 'parent': 'FUN_00401090'}
for l in local_var_list:
    var_name = l.get('name', l.get('var'))
    data_type = l.get('data_type', l.get('datatype'))
    
    local_var = pfs["mkg"][quote_for_turtle(var_name)]
    parent_func = pfs["mkg"][quote_for_turtle(l['parent'])]
    
    graph.add((local_var, a, LOCAL_VARIABLE))
    graph.add((parent_func, a, FUNCTION_NODE))
    # get the name of the function and add that relation
    graph.add((parent_func, hasName, Literal(str(l['parent']))))
    
    graph.add((parent_func, defines, local_var))
    graph.add((local_var, hasDataType, Literal(str(data_type))))

# Parameter format example:
# {'var': 'hModule', 'datatype': 'typedef HMODULE HINSTANCE', 'parent': 'GetProcAddress'}
for p in parameters_list:
    param_name = p.get('name', p.get('var'))
    data_type = p.get('data_type', p.get('datatype'))
    
    param = pfs["mkg"][quote_for_turtle(param_name)]
    parent_func = pfs["mkg"][quote_for_turtle(p['parent'])]
    
    graph.add((param, a, PARAMETER))
    graph.add((parent_func, a, FUNCTION_NODE))
    graph.add((parent_func, hasName, Literal(str(p['parent']))))
    
    graph.add((param, passesInto, parent_func))
    graph.add((param, hasDataType, Literal(str(data_type))))

# Namespace format example:
# {'namespace': 'switchD_0040f727', 'address': 'NO ADDRESS', 'parent': 'Global', 'references': [], 'primary_reference': None}
for n in namespace_list:
    ns_name = n.get('name', n.get('namespace'))
    parent_type = n.get('parent_type', n.get('parenttype'))
    
    n_instance = pfs["mkg"][quote_for_turtle(ns_name)]
    graph.add((n_instance, a, NAMESPACE))
    
    # add the address of namespace KG (both the address as an ADDRESS object, and the atAddress relation)
    if n['address'] != "NO ADDRESS":
        n_address = pfs["mkg"][quote_for_turtle(n['address'])]
        graph.add((n_address, a, ADDRESS))
        graph.add((n_instance, atAddress, n_address))
        
    # get the parent namespace of the current object
    n_parent = pfs["mkg"][quote_for_turtle(n['parent'])]
    # get the parent namespace type
    # if the given parent type is a type of symbol defined in the symbol class dictionary
    if parent_type in class_dict:
        # then get the URIRef for that type of class and make the triple defining the parent as that type of class.
        graph.add((n_parent, a, class_dict[parent_type]))
    # then add the definedIn relation for the current namespace and its parent namespace
    graph.add((n_instance, definedIn, n_parent))
    
    # if the namespace has any references, add them
    if n.get('references'):
        for r in n['references']:
            # method that will add a reference to the given object instance
            # false indicates that it's not a primary reference
            add_reference(n_instance, r, False)

    # add primary reference if it exists
    if n.get('primary_reference'):
        # same as previous, except now it's a primary reference so the third value is True
        add_reference(n_instance, n['primary_reference'], True)

# Class format example:
# {'class': 'type_info (GhidraClass)', 'address': 'NO ADDRESS', 'parent': 'Global', 'references': [], 'primary_reference': None} 
if class_list:
    for c in class_list:
        c_name = c.get('name', c.get('class'))
        parent_type = c.get('parent_type', c.get('parenttype'))
        
        c_instance = pfs["mkg"][quote_for_turtle(c_name)]
        graph.add((c_instance, a, CLASS_))
        
        if c['address'] != "NO ADDRESS":
            c_address = pfs["mkg"][quote_for_turtle(c['address'])]
            graph.add((c_address, a, ADDRESS))
            graph.add((c_instance, atAddress, c_address))
            
        c_parent = pfs["mkg"][quote_for_turtle(c['parent'])]    
        if parent_type in class_dict:
            graph.add((c_parent, a, class_dict[parent_type]))
        graph.add((c_instance, definedIn, c_parent)) 
        
        if c.get('references'):
            for r in c['references']:
                add_reference(c_instance, r, False)
            
        if c.get('primary_reference'):
            add_reference(c_instance, c['primary_reference'], True)

# DLL format example:
# {'dll': 'KERNEL32.DLL', 'address': 'NO ADDRESS parent:Global', 'references': [], 'primary_reference': None}
for l in dll_list:
    dll_name = l.get('name', l.get('dll'))
    parent_type = l.get('parent_type', l.get('parenttype'))
    
    l_instance = pfs["mkg"][quote_for_turtle(dll_name)]
    graph.add((l_instance, a, EXTERNAL_FUNCTION_NODE))
    
    if l['address'] != "NO ADDRESS":
        l_address = pfs["mkg"][quote_for_turtle(l['address'])]
        graph.add((l_address, a, ADDRESS))
        graph.add((l_instance, atAddress, l_address))
        
    l_parent = pfs["mkg"][quote_for_turtle(l['parent'])]
    if parent_type in class_dict:
        graph.add((l_parent, a, class_dict[parent_type])) 
    graph.add((l_instance, definedIn, l_parent))    
    
    if l.get('references'):
        for r in l['references']:
            add_reference(l_instance, r, False)
    if l.get('primary_reference'):
        add_reference(l_instance, l['primary_reference'], True)

# Function format example:
# {'func': 'GetTempPathW', 'address': 'EXTERNAL:00000005', 'returntype': 'typedef DWORD ulong', 'returnvalue': '[DWORD <RETURN>@EAX:4]', 
# 'parent': 'KERNEL32.DLL', 'functions_called': [], 
# 'references': [{'source': '00422018', 'destination': 'EXTERNAL:00000005', 'operandindex': '0', 'type': 'DATA'}, 
# {'source': '004012f0', 'destination': 'EXTERNAL:00000005', 'operandindex': '-1', 'type': 'COMPUTED_CALL'}], 
# 'primary_reference': {'source': '004012f0', 'destination': 'EXTERNAL:00000005', 'operandindex': '-1', 'type': 'COMPUTED_CALL'}} 
for f in function_list:
    f_name = f.get('name', f.get('func'))
    parent_type = f.get('parent_type', f.get('parenttype'))
    ret_type = f.get('return_type', f.get('returntype'))
    ret_val = f.get('return_value', f.get('returnvalue'))
    
    f_instance = pfs["mkg"][quote_for_turtle(f_name)]
    graph.add((f_instance, a, FUNCTION_NODE))
    graph.add((f_instance, hasName, Literal(str(f_name))))
    
    if f['address'] != "NO ADDRESS":
        f_address = pfs["mkg"][quote_for_turtle(f['address'])]
        graph.add((f_address, a, ADDRESS))
        graph.add((f_instance, atAddress, f_address))
        
    f_parent = pfs["mkg"][quote_for_turtle(f['parent'])]    
    if parent_type in class_dict:
        graph.add((f_parent, a, class_dict[parent_type]))
    graph.add((f_instance, definedIn, f_parent))
     
    # get all the functions called from this function
    called_funcs = f.get('called_functions', f.get('functions_called', []))
    if called_funcs:
        for fc in called_funcs:
            # make the URI of the function since it is seen elsewhere
            fc_name = fc if isinstance(fc, str) else fc.get('func')
            func_called = pfs["mkg"][quote_for_turtle(fc_name)]
            graph.add((func_called, a, FUNCTION_NODE))
            graph.add((func_called, hasName, Literal(str(fc_name))))
            graph.add((f_instance, calls, func_called))
            
    # return type
    graph.add((f_instance, hasReturnType, Literal(str(ret_type))))
    
    # return value (as a parameter)
    if ret_val:
        f_return_value = pfs["mkg"][quote_for_turtle(ret_val)]
        graph.add((f_return_value, a, PARAMETER))
        graph.add((f_instance, returns, f_return_value))
    
    # if any references exist, add them as triples
    if f.get('references'):
        for r in f['references']:
            add_reference(f_instance, r, False)
            
    if f.get('primary_reference'):
        add_reference(f_instance, f['primary_reference'], True)

# Label format example:
# {'label': 'shift', 'address': '00000000', 'parent': 'Global', 'parenttype': 'NAMESPACE', 'references': [], 'primary_reference': None}
for l in label_list:
    l_name = l.get('name', l.get('label'))
    parent_type = l.get('parent_type', l.get('parenttype'))
    
    # add address to the name to diffrentiate different labels with the same name
    # and do 2 underscores to differentiate between namespace names
    l_instance = pfs["mkg"][quote_for_turtle(l_name + "__" + l['address'])]
    graph.add((l_instance, a, LABEL))
    
    if l['address'] != "NO ADDRESS":
        l_address = pfs["mkg"][quote_for_turtle(l['address'])]
        graph.add((l_address, a, ADDRESS))
        graph.add((l_instance, atAddress, l_address))
        
    l_parent = pfs["mkg"][quote_for_turtle(l['parent'])]
    if parent_type in class_dict:
        graph.add((l_parent, a, class_dict[parent_type]))
    graph.add((l_instance, definedIn, l_parent)) 
       
    if l.get('references'):
        for r in l['references']:
            add_reference(l_instance, r, False)
    if l.get('primary_reference'):
        add_reference(l_instance, l["primary_reference"], True)

# Instruction format example:
# {'min_address': '00401090', 'opcode': 'PUSH', 'in_function': 'FUN_00401090', 'numoperands': '1', 
# 'source_operands': [{'operand': 'EBP', 'type': 'REGISTER'}], 
# 'destination_operand': {'operand': 'EBP', 'type': 'REGISTER'}}
for i in instruction_list:
    i_instance = pfs["mkg"]["ins_" + str(i["min_address"])]
    graph.add((i_instance, a, INSTRUCTION))
    
    i_address = pfs["mkg"][quote_for_turtle(i['min_address'])]
    graph.add((i_address, a, ADDRESS))
    graph.add((i_instance, atAddress, i_address))
    
    # opcode
    opcode = Literal(i["opcode"])
    graph.add((i_instance, hasOpcode, opcode))
    
    # Process structured operands from JSON
    operands = i.get('operands', [])
    for op in operands:
        operand = pfs["mkg"][quote_for_turtle(op['representation'])]
        graph.add((operand, a, OPERAND))
        
        op_type = Literal(str(op["type"]))
        graph.add((operand, hasOperandType, op_type))
        graph.add((operand, hasOperandValue, Literal(op['representation'])))
        
        role = op.get('role', '')
        if role in ['SOURCE', 'SOURCE_AND_DESTINATION']:
            graph.add((i_instance, hasSourceOperand, operand))
        if role in ['DESTINATION', 'SOURCE_AND_DESTINATION']:
            graph.add((i_instance, hasDestinationOperand, operand))
        
    # get whatever function has this instruction
    func = pfs["mkg"][quote_for_turtle(i['in_function'])]
    # then add the function contains instruction relation with the current instruction
    graph.add((func, a, FUNCTION_NODE))
    graph.add((func, hasName, Literal(str(i['in_function']))))
    graph.add((func, containsInstruction, i_instance))    


# =================== Knowledge node materialization ========================
# get all the list of dictionaries from the json files
# (reuse dir_path — reassigning script_dir here shadowed the scripts directory
# computed above, which is needed for anything resolved relative to the script)
binary_path = dir_path / "binaries.json"
binary_list = load_nodes(str(binary_path))

func_path = dir_path / "function-node.json"
func_list = load_nodes(str(func_path))

ext_path = dir_path / "externals.json"
ext_list = load_nodes(str(ext_path))

module_path = dir_path / "modules.json"
module_list = load_nodes(str(module_path))

# Then add the triples for all 4 kinds of knowledge nodes
for function in func_list:
    materialize_knowledge_node(function, "FUNCTION")
          
for external in ext_list:
    materialize_knowledge_node(external, "EXTERNAL")
    
for module in module_list:
    materialize_knowledge_node(module, "MODULE")

for binary in binary_list:
    materialize_knowledge_node(binary, "BINARY")

# then serialize the graph
output_file = str(dir_path / "combined-output.ttl")
temp = graph.serialize(format="turtle", encoding="utf-8", destination=output_file)
print("Wrote: %s" % output_file)
print("Finished materializing. Exiting...")