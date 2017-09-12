import os
import json
import subprocess
import sys
from nipype.utils.filemanip import (load_json, save_json, split_filename, fname_presuffix, copyfile)
from nipype.utils.filemanip import loadcrash
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom


sys.path.append("/opt/")
minc2volume=__import__("minc2volume-viewer")

def cmd(command):
    return subprocess.check_output(command.split(), universal_newlines=True).strip()

def mnc2vol(mincfile):
    image_precision = cmd("mincinfo -vartype image {}".format(mincfile)).replace("_","")
    image_signtype = cmd("mincinfo -attvalue image:signtype {}".format(mincfile)).replace("_","")
    datatype = {
        "byte signed" : "int8",
        "byte unsigned" : "uint8",
        "short signed" : "int16",
        "short unsigned" : "uint16",
        "int signed" : "int32",
        "int unsigned" : "uint32",
        "int signed" : "int32",
        "int unsigned" : "uint32",
        "float signed" : "float32",
        "float" : "float32",
        "double" : "float64",
    }[str(image_precision+" "+image_signtype)]
    rawfile=mincfile+'.raw'
    headerfile=mincfile+'.header'
    minc2volume.make_raw(mincfile, datatype, rawfile)
    minc2volume.make_header(mincfile, datatype, headerfile)

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='UTF-8')




listOfNodes = [
    {"name" : "t1Masking", 
     "mnc_inputs" : ['nativeT1'],
     "mnc_outputs" : ['T1headmask','T1brainmask'],
    },
    {"name" : "petMasking", 
     "mnc_inputs" : ['in_file'],
     "txt_inputs" : ['in_json'],
     "mnc_outputs" : ['out_file']
    },
    {"name" : "refMasking", 
     "mnc_inputs" : ['nativeT1','T1Tal'],
     "mnc_outputs" : ['RegionalMaskTal','RegionMaskT1']
    },
    {"name" : "roiMasking", 
     "mnc_inputs" : ['nativeT1','T1Tal'],
     "mnc_outputs" : ['RegionalMaskTal','RegionMaskT1'],
    },
    {"name" : "petVolume", 
     "mnc_inputs" : ['in_file'],
     "mnc_outputs" : ['out_file']
    },
    {"name" : "pet2mri", 
     "mnc_inputs" : ['in_target_mask','in_target_file','in_source_mask','in_source_file'],
     "mnc_outputs" : ['out_file_img']
    },
    {"name" : "gtm", 
     "mnc_inputs" : ['input_file'],
     "mnc_outputs" : ['out_file']
    },
    {"name" : "fixHeaderNode", 
     "mnc_outputs" : ['out_file']
    }
]



outputDir="/opt/raclo/out/"
filename=outputDir+"preproc/graph1.json";
fp = file(filename, 'r')
data=json.load(fp)
fp.close()

xmlQC = Element('qc')
listVolumes = list();
for subjIdx in range(0,len(data["groups"])-1):
    nodeID = data["groups"][subjIdx]["procs"][0]-1
    nodeName = data["nodes"][nodeID]["name"][len(str(nodeID))+1:]
    while nodeName != "datasourceRaw":
        nodeID+=1;
        nodeName = data["nodes"][nodeID]["name"][len(str(nodeID))+1:]
    nodeReport = loadcrash(outputDir+"preproc/"+data["nodes"][nodeID]["result"])
    for key, value in nodeReport.inputs.items():
        if key == "study_prefix":
            study_prefix = str(value)
        if key == "cid":
            cid = str(value)
        if key == "sid":
            sid = str(value)
    xmlscan = SubElement(xmlQC, 'scan')
    xmlscan.set('prefix', study_prefix)
    xmlscan.set('sid', sid)
    xmlscan.set('cid', cid)
    for nodeID in range(data["groups"][subjIdx]["procs"][0],data["groups"][subjIdx]["procs"][-1]):
        nodeName = data["nodes"][nodeID]["name"][len(str(nodeID))+1:]
        if nodeName in [x['name'] for x in listOfNodes]:

            print nodeName
            print outputDir+"preproc/"+data["nodes"][nodeID]["result"]
            nodeReport = loadcrash(outputDir+"preproc/"+data["nodes"][nodeID]["result"])
            xmlnode = SubElement(xmlscan, 'node')
            xmlnode.set('name', nodeName)
            if listOfNodes[[x['name'] for x in listOfNodes].index(nodeName)].has_key("mnc_inputs"):
                xmlinmnc = SubElement(xmlnode, 'inMnc')
                for key, value in nodeReport.inputs.items():
                    if key in listOfNodes[[x['name'] for x in listOfNodes].index(nodeName)]['mnc_inputs']:
#                                 xmlkey = SubElement(xmlinmnc, str(key))
#                                 xmlkey.text = str(value)
#                                 listVolumes.append(value)
                        xmlkey = SubElement(xmlinmnc, str(key))
                        xmlkey.text = str(value)[27:]
                        listVolumes.append(str(value)[27:])
            if listOfNodes[[x['name'] for x in listOfNodes].index(nodeName)].has_key("mnc_outputs"):
                xmloutmnc = SubElement(xmlnode, 'outMnc')
                for key, value in nodeReport.outputs.items():
                    if key in listOfNodes[[x['name'] for x in listOfNodes].index(nodeName)]['mnc_outputs']:
#                                 xmlkey = SubElement(xmloutmnc, str(key))
#                                 xmlkey.text = str(getattr(nodeReport.outputs,key))
#                                 listVolumes.append(getattr(nodeReport.outputs,key))
                        xmlkey = SubElement(xmloutmnc, str(key))
                        xmlkey.text = str(getattr(nodeReport.outputs,key))[27:]
                        listVolumes.append(str(getattr(nodeReport.outputs,key))[27:])


#             try:
#                 print nodeName
#                 print outputDir+"preproc/"+data["nodes"][nodeID]["result"]
#                 nodeReport = loadcrash(outputDir+"preproc/"+data["nodes"][nodeID]["result"])
#                 try:
#                     xmlnode = SubElement(xmlscan, 'node')
#                     xmlnode.set('name', nodeName)
#                     if listOfNodes[[x['name'] for x in listOfNodes].index(nodeName)].has_key("mnc_inputs"):
#                         xmlinmnc = SubElement(xmlnode, 'inMnc')
#                         for key, value in nodeReport.inputs.items():
#                             if key in listOfNodes[[x['name'] for x in listOfNodes].index(nodeName)]['mnc_inputs']:
# #                                 xmlkey = SubElement(xmlinmnc, str(key))
# #                                 xmlkey.text = str(value)
# #                                 listVolumes.append(value)
#                                 xmlkey = SubElement(xmlinmnc, str(key))
#                                 xmlkey.text = str(value)[27:]
#                                 listVolumes.append(str(value)[27:])
#                     if listOfNodes[[x['name'] for x in listOfNodes].index(nodeName)].has_key("mnc_outputs"):
#                         xmloutmnc = SubElement(xmlnode, 'outMnc')
#                         for key, value in nodeReport.outputs.items():
#                             if key in listOfNodes[[x['name'] for x in listOfNodes].index(nodeName)]['mnc_outputs']:
# #                                 xmlkey = SubElement(xmloutmnc, str(key))
# #                                 xmlkey.text = str(getattr(nodeReport.outputs,key))
# #                                 listVolumes.append(getattr(nodeReport.outputs,key))
#                                 xmlkey = SubElement(xmloutmnc, str(key))
#                                 xmlkey.text = str(getattr(nodeReport.outputs,key))[27:]
#                                 listVolumes.append(str(getattr(nodeReport.outputs,key))[27:])
#                 except :
#                     print("Cannot write the XML field for the node "+nodeName+"\n")
#             except :
#                 print("Error to load the pickle file"+"\n")
 
    
print prettify(xmlQC)
with open("/opt/raclo/nodes.xml","w") as f:
    f.write(prettify(xmlQC))

for vol in listVolumes:
    print vol
    # mnc2vol(vol)