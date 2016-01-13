import maya.cmds as cmds
import json
import os
import math

component = {
    "id":0,
    "type":"",
    "src":"",
    "connectors":[]
}

furniture = None

jsonRepresentationInput = None
componentsMenu = None
componentTypeInput = None
typeInput = None
objNameInput = None
loadComponentsMenu = None

furnitureFile = None
furnitureFilePath = None

def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def loadFurniture():
    filename = cmds.fileDialog2(fileMode=1, fileFilter="*.json", caption="Open Furniture JSON")
    global furnitureFile
    global furnitureFilePath
    furnitureFilePath = filename[0]
    furnitureFile = open(filename[0], "a+")
    furnJson = furnitureFile.read()
    global furniture
    furniture = json.loads(furnJson)

    menuItems = cmds.optionMenu(loadComponentsMenu, q=True, itemListLong=True)
    
    if menuItems:
        cmds.deleteUI(menuItems)

    for comp in furniture['components']:
        cmds.menuItem(p=loadComponentsMenu, label=comp["type"] + "-" + comp["src"])

def loadSelectedObj():
    cmds.file(new=True, pm=False, force=True)
    selected = cmds.optionMenu(loadComponentsMenu, q=True, v=True).split("-")[1]
    global furniture
    global furnitureFilePath
    path = os.path.split(furnitureFilePath)[0] + "/meshes/furniture/"
    menuItems = cmds.optionMenu(componentsMenu, q=True, itemListLong=True)
    cmds.textField(objNameInput, tx=path + selected, e=True)
    if menuItems:
        cmds.deleteUI(menuItems)
    for comp in furniture["components"] :
        if comp["src"] == selected :
            cmds.file(path + selected, i=True)    
            global component 
            component = comp
            for con in component["connectors"]:
                cmds.menuItem(p=componentsMenu, label=con["componentType"])
                for pos in con["positions"]:
                    loc = cmds.spaceLocator()
                    cmds.move(pos["positionX"], pos["positionY"], pos["positionZ"], loc )
    updateJson()
    selectLocators()
    cmds.textField(typeInput, tx=component["type"], e=True)

def updateJson():
    cmds.textField(jsonRepresentationInput, text=json.dumps(component), e=True)

def getConnectorTypes():
    types = []
    for con in component["connectors"]:
        types.append(con["componentType"])
    return types


def getConnectorForType(compType):
    for con in component["connectors"]:
        if con["componentType"] == compType:
            return con
    return None


def selectLocators():
    cmds.select(clear=True)
    selected = cmds.optionMenu(componentsMenu, q=True, v=True)
    objects = cmds.ls(tr=True)
    for pos in getConnectorForType(selected)["positions"]:
        for obj in objects:
            trans = cmds.xform(obj, q=1, ws=1, rp=1)
            print pos 
            print trans 
            if isclose(round(trans[0], 3), round(pos["positionX"], 3)) and isclose(round(trans[1], 3), round(pos["positionY"], 3)) and isclose(round(trans[2], 3), round(pos["positionZ"], 3)):
                cmds.select(obj, add=True)


def updateComponentType():
    component["type"] = cmds.textField(typeInput, q=True, tx=True).lower()
    updateJson()

def addOutComp():
    newType = cmds.textField(componentTypeInput, tx=True, q=True)
    if(getConnectorForType(newType) == None):
        if(len(newType) > 0):
            newType = newType.lower()
            newConnector = {"componentType":newType, "positions":[]}
            component["connectors"].append(newConnector)

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
    if connector != None:
        locators = cmds.ls(transforms=True, selection=True)
        for locator in locators:
            trans = cmds.xform(locator, q=1, ws=1, rp=1)
            pos = {}
            pos["positionX"] = trans[0]
            pos["positionY"] = trans[1]
            pos["positionZ"] = trans[2]
            connector["positions"].append(pos)

        updateJson()
    else :
        cmds.error("Connector Type is invalid")

def exportObj():
    try:
        fileName = cmds.textField(objNameInput, q=True, tx=True).split(".")[0] + ".obj"
        cmds.file("c:/" + fileName, pr=1, typ="OBJexport", es=1, op="groups=0; ptgroups=0; materials=0; smoothing=0; normals=1")
    except:
        cmds.error("Could not save OBJ - Make sure the plugin is loaded")

if 'window' in globals():
    if cmds.window(window, exists=True):
        cmds.deleteUI(window, window=True)

window = cmds.window(title='Furniture Component Builder', width=500, height=500)

cmds.columnLayout(adjustableColumn=True)

cmds.button("Load Furniture Definitions", command='loadFurniture()')

cmds.rowLayout(nc=2, adjustableColumn=True)
loadComponentsMenu = cmds.optionMenu()
cmds.button(label='Load Component', command='loadSelectedObj()')
cmds.setParent('..')

cmds.text( label='Type' )
typeInput = cmds.textField(cc="updateComponentType()")

cmds.rowLayout(nc=2, adjustableColumn=True)
componentsMenu = cmds.optionMenu(cc="selectLocators()")
cmds.button(label='Set Connectors', command='genConnectors()')
cmds.setParent('..')

cmds.rowLayout(nc=2, adjustableColumn=True)
cmds.columnLayout(adjustableColumn=True)
cmds.text( label='New Out Component Type' )
componentTypeInput = cmds.textField()
cmds.setParent('..')
cmds.button(label='Add Connector Type', command='addOutComp()')
cmds.setParent('..')

cmds.rowLayout(nc=2, adjustableColumn=True)
cmds.columnLayout(adjustableColumn=True)
cmds.text( label='JSON' )
jsonRepresentationInput = cmds.textField()
cmds.setParent('..')
cmds.button(label='Save JSON', command='saveJson()')
cmds.setParent('..')

cmds.rowLayout(nc=2, adjustableColumn=True)
cmds.columnLayout(adjustableColumn=True)
cmds.text( label='OBJ File Name' )
objNameInput = cmds.textField()
cmds.setParent('..')
cmds.button(label='Save OBJ', command='exportObj()')
cmds.setParent('..')

cmds.setParent('..')

cmds.showWindow(window)



