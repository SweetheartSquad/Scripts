import maya.cmds as cmds
import json
import os
import math
import logging

logging.basicConfig(level=logging.DEBUG)

if 'window' in globals():
    if cmds.window(window, exists=True):
        cmds.deleteUI(window, window=True)

currentComponent = None
furniture = None

jsonRepresentationInput = None
currentComponentsMenu = None
currentComponentTypeInput = None
typeInput = None
objNameInput = None
loadcurrentComponentsMenu = None
loadFurnitureButton = None
layout = None
window = cmds.window(title='Furniture currentComponent Builder', width=500, height=500)

furnitureFile = None
furnitureFilePath = None


def initUi():

    global currentComponent
    currentComponent = {
        "id":0,
        "type":"",
        "src":"",
        "connectors":[
            {"componentTypes":[],
            "out":[
                {
                    "position":[],
                    "scale":[],
                    "rotation":[]
                }
            ]}
        ]
    }

    global window
    if cmds.window(window, exists=True):
        cmds.deleteUI(window, window=True)
        window = cmds.window(title='Furniture Component Builder', width=500, height=500)

    layout = cmds.columnLayout(adjustableColumn=True)

    cmds.button(label='New Component', command='loadFurniture(furnitureFilePath)')

    cmds.rowLayout(nc=2, adjustableColumn=True)
    global loadComponentsMenu
    loadComponentsMenu = cmds.optionMenu()
    cmds.button(label='Load Component', command='loadSelectedObj()')
    cmds.setParent('..')

    cmds.text( label='Type' )
    global typeInput
    typeInput = cmds.textField(cc="updateComponentType()")

    cmds.rowLayout(nc=2, adjustableColumn=True)
    global componentsMenu
    componentsMenu = cmds.optionMenu(cc="selectLocators()")
    cmds.button(label='Set Connectors', command='genConnectors()')
    cmds.setParent('..')

    cmds.rowLayout(nc=2, adjustableColumn=True)
    cmds.columnLayout(adjustableColumn=True)
    cmds.text( label='New Connector Type' )
    global componentTypeInput
    componentTypeInput = cmds.textField()
    cmds.setParent('..')
    cmds.button(label='Add Connector Type', command='addOutComp()')
    cmds.setParent('..')

    cmds.rowLayout(nc=2, adjustableColumn=True)
    cmds.columnLayout(adjustableColumn=True)
    cmds.text( label='JSON' )
    global jsonRepresentationInput
    jsonRepresentationInput = cmds.textField()
    cmds.setParent('..')
    cmds.button(label='Save JSON', command='saveJson()')
    cmds.setParent('..')

    cmds.rowLayout(nc=2, adjustableColumn=True)
    cmds.columnLayout(adjustableColumn=True)
    cmds.text( label='OBJ File Name' )
    global objNameInput
    objNameInput = cmds.textField(cc="objChange()")
    cmds.setParent('..')
    cmds.button(label='Save OBJ', command='exportObj()')
    cmds.setParent('..')

    cmds.setParent('..')

    menuItems = cmds.optionMenu(loadComponentsMenu, q=True, itemListLong=True)
    if menuItems:
        cmds.deleteUI(menuItems)
    cmds.showWindow(window)

#deals with floating pointers
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def loadFurniture(filePath=None):
    #cmds.file(new=True, pm=False, force=True)
    if(filePath == None):
        filename = cmds.fileDialog2(fileMode=1, fileFilter="*.json", caption="Open Furniture JSON")
        global furnitureFile
        global furnitureFilePath
        furnitureFilePath = filename[0]
        with open(filename[0], "r") as furnitureFile:
            furnJson = furnitureFile.read()
        global furniture
        furniture = json.loads(furnJson)
        cmds.deleteUI(loadFurnitureButton)

    initUi()

    id = 0
    for comp in furniture['components']:

        cmds.menuItem(p=loadComponentsMenu, label=comp["src"])
        id = max(id, comp["id"])
    id += 1
    currentComponent['id'] = id

def loadSelectedObj():
    cmds.file(new=True, pm=False, force=True)
    selected = cmds.optionMenu(loadComponentsMenu, q=True, v=True)
    global furniture
    global furnitureFilePath
    path = os.path.split(furnitureFilePath)[0] + "/meshes/furniture/"
    menuItems = cmds.optionMenu(componentsMenu, q=True, itemListLong=True)
    cmds.textField(objNameInput, tx=selected.split(".")[0], e=True)
    if menuItems:
        cmds.deleteUI(menuItems)
    for comp in furniture["components"] :
        if comp["src"] == selected :
            global currentComponent
            componentDef = ""

            with open(os.path.split(furnitureFilePath)[0]+"/"+comp["src"], "r") as componentFile:
                componentDef = componentFile.read()
            currentComponent = json.loads(componentDef)

            cmds.file(path + currentComponent["src"], i=True)
            for con in currentComponent["connectors"]: #for connectors in the current objects connectors
                for types in con["componentTypes"]:
                    cmds.menuItem(p=componentsMenu, label=types)
                for jnt in con["out"]:
                    loc = cmds.spaceLocator()
                    cmds.move(jnt["position"][0], jnt["position"][1], jnt["position"][2], loc)
                    cmds.scale(jnt["scale"][0], jnt["scale"][1], jnt["scale"][2], loc)
                    cmds.rotate(jnt["rotation"][0], jnt["rotation"][1], jnt["rotation"][2], loc)
    updateJson()
    selectLocators()
    cmds.textField(typeInput, tx=currentComponent["type"], e=True)

def updateJson():
    cmds.textField(jsonRepresentationInput, text=json.dumps(currentComponent), e=True)

def objChange():
    textVal = cmds.textField(objNameInput, q=True, tx=True)
    currentComponent["src"] = textVal + ".obj"
    updateJson()


def getConnectorTypes():
    types = []
    for con in currentComponent["connectors"]: # for connectors within the current component object
        for compTypes in con["componentTypes"]: #for the component types that connect to the object, add them to the types array and return
            types.append(compTypes)
    return types


def getConnectorForType(compType):
    for con in currentComponent["connectors"]: # for connectors within the current component object
        for compTypes in con["componentTypes"]: #for the component types that connect to the object
            if compTypes == compType: #if the component type match with the component type passed into function
                print con
                return con #return the connecting component
    return None


def selectLocators():
    cmds.select(clear=True)
    selected = cmds.optionMenu(componentsMenu, q=True, v=True) #selected equals select option in componenetsMenu
    objects = cmds.ls(tr=True) #create objects list
    for out in selected: #for out object (see json) in selected, get the positions of the connectors
        for outCon in getConnectorForType(selected)["out"]: #for each out objects, get the position which is an array of x,y,z,
             for pos in outCon["position"]:   
                for obj in objects: #for obj in objects list compare them to the components in the scene and see if they match up
                    trans = cmds.xform(obj, q=1, ws=1, rp=1)
                    if isclose(round(trans[0], 3), round(outCon["position"][0], 3)) and isclose(round(trans[1], 3), round(outCon["position"][1], 3)) and isclose(round(trans[2], 3), round(outCon["position"][2], 3)):
                        cmds.select(obj, add=True)


def updateComponentType():
    currentComponent["type"] = cmds.textField(typeInput, q=True, tx=True).lower()
    updateJson()

def addOutComp():
    newType = cmds.textField(componentTypeInput, tx=True, q=True)
    if(getConnectorForType(newType) == None):
        if(len(newType) > 0):
            newType = newType.lower()
            newConnector = {"componentType":newType, "out":{"position":[],"scale":[],"rotation":[]}}
            currentComponent["connectors"].append(newConnector)

            menuItems = cmds.optionMenu(componentsMenu, q=True, itemListLong=True)

            if menuItems:
                cmds.deleteUI(menuItems)
            for comp in getConnectorTypes() :
                cmds.menuItem(p=componentsMenu, label=comp)

            updateJson()
        else:
            cmds.error("Connector Type cannot be blank")
    else:
        cmds.error("Connector Type already exists")


def genConnectors():
    connector = getConnectorForType(cmds.optionMenu(componentsMenu, q=True, v=True))
    connector["out"]["position"] = []
    if connector != None:
        locators = cmds.ls(transforms=True, selection=True)
        for locator in locators:
            trans = cmds.xform(locator, q=1, ws=1, rp=1)
            rot = cmds.xform(locator, q=1, ws=1, ro=1)
            scal = cmds.xform(locator, q=1, ws=1, s=1)
            connector["out"]["position"].append(trans)
            connector["out"]["rotation"].append(rot)
            connector["out"]["scale"].append(scal)

        updateJson()
    else :
        cmds.error("Connector Type is invalid")

def exportObj():
    try:
        fileName = cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".obj"
        cmds.file(os.path.split(furnitureFilePath)[0] + "/meshes/furniture/" + fileName, pr=1, typ="OBJexport", es=1, op="groups=0; ptgroups=0; materials=0; smoothing=0; normals=1")
        logging.info("Obj Save Success")
    except:
        cmds.error("Could not save OBJ - Make sure the plugin is loaded")

def saveJson():

    typeVal = cmds.textField(typeInput, tx=True, q=True)

    if len(typeVal) == 0:
        cmds.error("Type must be specifed")
        return

    objFile = cmds.textField(objNameInput, tx=True, q=True)

    if len(objFile) == 0:
        cmds.error("Obj file must be specified")
    else:
        if not os.path.isfile(os.path.split(furnitureFilePath)[0] + "/meshes/furniture/" + objFile + ".obj"):
            cmds.error("Obj file must exist")
            return

    found = False
    for comp in furniture["components"]:
        if comp["id"] == currentComponent["id"]:
            found = True
            comp = currentComponent
            fileName = cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".obj"
            with open(os.path.split(furnitureFilePath)[0] + "/furnitureJson/"+cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".json", "w+") as furnitureFile:
                furnitureFile.write(json.dumps(furniture, indent=4, sort_keys=True))
                logging.info("Json Save Success")
            comp["src"] = fileName
            print os.path.split(furnitureFilePath)[0] + "/furnitureJson/"+cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".json"
    if not found:
        comp = currentComponent
        fileName = cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".obj"
        with open(os.path.split(furnitureFilePath)[0] + "/furnitureJson/"+cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".json", "w+") as furnitureFile:
            furnitureFile.write(json.dumps(comp, indent=4, sort_keys=True))
            logging.info("Json Save Success")
        comp["src"] = fileName
        newFurniture = {'id':currentComponent["id"],"src":"furnitureJson/"+cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".json"}
        furniture["components"].append(newFurniture)
        print os.path.split(furnitureFilePath)[0] + "/furnitureJson/"+cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".json"



    with open(furnitureFilePath, "w+") as furnitureFile:
        furnitureFile.write(json.dumps(furniture, indent=4, sort_keys=True))
        logging.info("Json Save Success")

layout = cmds.columnLayout(adjustableColumn=True)

loadFurnitureButton = cmds.button("Load Furniture Definitions", command='loadFurniture()')

cmds.showWindow(window)

