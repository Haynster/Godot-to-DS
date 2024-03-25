import json
import os
import shutil
from PIL import Image
import random

fullJSON = {}

def convertScene(fileName):
    # Variables
    nodeSelected = False
    scanningText = False

    currentNodeName = ""
    currentNodeJSON = {}
    currentResJSON = {}
    sceneJSON = {}

    nodes = {}
    resources = {}

    result = {}

    # Do It
    file = open(fileName, "r")
    tscn = file.readlines()
    tscn.append("\n")

    nodeStructure = {}

    for x in tscn:
        print("anotehr line")
        if x[0] == "[":
            # Create array of current line elements
            trim_result = x[1:-2]
            split_result = trim_result.split('" ')
            for i, n in enumerate(split_result):
                if not n[len(n) - 1] == '"':
                    split_result[i] = str(split_result[i]) + '"'
            resourceType = split_result[0].split(" ")[0]
            split_result.insert(1, split_result[0].split(" ")[1])
            # Create JSON of the node
            if resourceType == "node":
                print("working node")
                nodeSelected = True
                currentNodeName = split_result[1].split("=")[1][1:-1]
                currentNodeJSON["name"] = currentNodeName
                currentNodeJSON["type"] = split_result[2].split("=")[1][1:-1]
                if len(split_result) > 3:
                    currentNodeJSON["parent"] = split_result[3].split("=")[1][1:-1]
                    nodeStructure[split_result[3].split("=")[1][1:-1]] = split_result[1].split("=")[1][1:-1]
                    currentNodeName = split_result[3].split("=")[1][1:-1] + "/" + split_result[1].split("=")[1][1:-1]
                    currentNodeJSON["name"] = currentNodeName
                    print(currentNodeJSON)
                else:
                    currentNodeJSON["parent"] = "root"
                    nodeStructure["root"] = split_result[1].split("=")[1][1:-1]
                    currentNodeName = "/" + split_result[1].split("=")[1][1:-1]
                    currentNodeJSON["name"] = currentNodeName
            # Create JSON of a resource
            if resourceType == "ext_resource":
                currentResJSON = {}
                if len(split_result) == 4:
                    currentResJSON["type"] = split_result[1].split("=")[1][1:-1]
                    currentResJSON["path"] = split_result[2].split("=")[1][1:-1]
                    currentResJSON["id"] = split_result[3].split("=")[1][1:-1]
                    resources[split_result[3].split("=")[1][1:-1]] = currentResJSON
                if len(split_result) == 5:
                    currentResJSON["type"] = split_result[1].split("=")[1][1:-1]
                    currentResJSON["uid"] = split_result[2].split("=")[1][1:-1]
                    currentResJSON["path"] = split_result[3].split("=")[1][1:-1]
                    currentResJSON["id"] = split_result[4].split("=")[1][1:-1]
                    resources[split_result[4].split("=")[1][1:-1]] = currentResJSON
            # Create JSON of scene
            if resourceType == "gd_scene":
                sceneJSON["loadSteps"] = trim_result.split(' ')[1].split("=")[1][1:-1]
                sceneJSON["format"] = trim_result.split(' ')[2].split("=")[1][1:-1]
                sceneJSON["uid"] = trim_result.split(' ')[3].split("=")[1][1:-1]
        elif x.isspace():
            # When reach empty line, save individual node JSON to big one
            if nodeSelected and not scanningText:
                print("node finished")
                nodes[currentNodeName] = currentNodeJSON
                print(currentNodeJSON)
                nodeSelected = False
                scanningText = False

                currentNodeName = ""
                currentNodeJSON = {}
                currentResJSON = {}
                sceneJSON = {}
        else:
            if nodeSelected and " = " in x:
                currentNodeJSON[x.split(" = ")[0]] = x.split(" = ")[1][:-1]

    result["nodes"] = nodes
    result["resources"] = resources
    result["scene"] = sceneJSON
    result["node_structure"] = nodeStructure
    return(str(json.dumps(result)))

def convertProject(projectFile):
    projectJSON = {}
    scanning = ""
    file = open(projectFile, "r")
    project = file.readlines()
    for x in project:
        if x == "[application]\n":
            scanning = "app"
        elif x == "[rendering]\n":
            scanning = "ren"
        elif x.isspace():
            pass
        else:
            if scanning == "app" and len(x.split("=")) > 1:
                projectJSON[x.split("=")[0]] = x.split("=")[1][:-1]
    return(projectJSON)

def convertPosition(pos, ogscreensize, screensize, offset):
    return(round(((pos / ogscreensize) * screensize) - offset))

def convertObjectReference(line, nodesJSON):
    if len(line[1:len(line)].split(".")[0].split("/")) > 0:
        modifiedNode = "./" + line[1:len(line)].split(".")[0].split("/")[0]
    else:
        modifiedNode = line[1:len(line)].split(".")[0].split("/")[len(line[1:len(line)].split(".")[0].split("/")) - 1] + "/" + line[1:len(line)].split(".")[0].split("/")[len(line[1:len(line)].split(".")[0].split("/"))]
    random.seed(nodesJSON[modifiedNode]["name"])
    nodeCount = round(random.random() * 9999)
    nodeName = nodesJSON[modifiedNode]["type"] + str(nodeCount)
    objectReference = line[1:len(line)].split(" = ")[0].split(".")
    resconstructedObjectReference = ""
    for x in objectReference:
        if not x == objectReference[0] and not x == objectReference[-1]:
            resconstructedObjectReference = resconstructedObjectReference + x + "_"
        elif x == objectReference[-1]:
            resconstructedObjectReference = resconstructedObjectReference + x
    return(nodeName + "_" + resconstructedObjectReference)

def convertFunction(x):
    func = ""
    if x.split("(")[0] == "len":
        func = func + "string." + x
    else:
        func = '""'
    return(func)

def convertScript(scriptFile, scriptNode, nodesJSON):
    code = []
    variables = {}
    functions = {}

    file = open(scriptFile, "r")
    if os.path.exists(scriptFile):
        script = file.readlines()
        script.append("")
        currentFunction = "nothing"
        declaringFunction = False
        ifLevels = []
        newlines = 0
        for l in script:
            line = ""
            compiliedLine = ""
            oldNewLines = newlines
            newlines = 0
            for c in l:
                if not c == "\t" and not c == "\n":
                    line = line + c
                elif c == "\t":
                    newlines = newlines + 1

            tabs = ""
            for t in range(0, newlines):
                tabs = tabs + "\t"

            # Do different things for dofferent pieces of code in the script
            if line[:5] == "print":
                compiliedLine = "Debug.print(" + line[6:len(line) - 1] + ')'
            elif line[:5] == "func ":
                currentFunction = line[5:len(line) - 1]
                compiliedLine = "function " + currentFunction
                functions[currentFunction.split("(")[0]] = ""
                declaringFunction = True
            elif line[:1] == "$":
                print(line)
                nodeName = convertObjectReference(line, nodesJSON)
                print(nodeName)
                if len(line.split(" = ")) > 1:
                    transformType = line.split(" = ")[0].split(".")[1]
                    print(transformType)
                    transformValue = line.split(" = ")[1]
                else:
                    transformType = line.split(".")[0]
                    print(transformType)
                    transformValue = line.split(".")[1]
                if transformType == "position":
                    if transformValue[:8] == "Vector2(":
                        print(transformValue)
                        transformX = transformValue[8:len(transformValue) - 1].split(", ")[0]
                        transformY = transformValue[8:len(transformValue) - 1].split(", ")[1]
                        if not transformX.isnumeric():
                            for x in transformX.split(" "):
                                reconstructedTransformX = ""
                                if x.isnumeric():
                                    reconstructedTransformX = reconstructedTransformX + str(convertPosition(int(x), 1152, 341, 42.5))
                                else:
                                    if x[:1] == "$":
                                        reconstructedTransformX = convertObjectReference(x, nodesJSON)
                                    else:
                                        reconstructedTransformX = reconstructedTransformX + x
                            print(reconstructedTransformX, "YEAHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
                            transformX = reconstructedTransformX
                        else:
                            transformX = str(convertPosition(int(transformX), 1152, 341, 42.5))
                        if not transformY.isnumeric():
                            for x in transformY.split(" "):
                                reconstructedTransformY = ""
                                if x.isnumeric():
                                    reconstructedTransformY = reconstructedTransformY + str(convertPosition(int(x), 648, 192, 0))
                                else:
                                    if x[:1] == "$":
                                        reconstructedTransformY = convertObjectReference(x, nodesJSON)
                                    else:
                                        reconstructedTransformY = reconstructedTransformY + x
                            print(reconstructedTransformY)
                            transformY = reconstructedTransformY
                        else:
                            transformY = str(convertPosition(int(transformY), 648, 192, 0))
                    else:
                        transformX = transformValue + "_vector_x"
                        transformY = transformValue + "_vector_y"
                    compiliedLine = [nodeName + "_x = " + str(transformX), nodeName + "_y = " + str(transformY)]
                    print(compiliedLine)
                elif transformType == "text":
                    if len(transformValue.split("[")) > 1:
                        compiliedLine = nodeName + " = " + convertObjectReference(transformValue, nodesJSON)
                        reconstructedLine = ""
                        for x in compiliedLine.split(" = ")[1].split(" "):
                            if x == "+":
                                reconstructedLine = reconstructedLine + ".. "
                            elif len(x.split("[")) > 1:
                                reconstructedLine = reconstructedLine + "string.sub(" + x.split("[")[0] + ", " + x.split("[")[1][:-1] + ", " + x.split("[")[1][:-1] + ")"
                            else:
                                reconstructedLine = reconstructedLine + x + " "
                                
                            if x == compiliedLine.split(" = ")[len(compiliedLine.split(" = ")) - 1]:
                                reconstructedLine = reconstructedLine[:-1]
                        compiliedLine = nodeName + " = " + reconstructedLine
                    else:
                        compiliedLine = nodeName + " = " + transformValue
                elif transformType == "visible":
                    compiliedLine = nodeName + " = " + transformValue
            elif line[:3] == "var":
                variableValue = line[4:len(line)].split(" = ")[1]
                if variableValue[:8] == "Vector2(":
                    vectorNameX = line[4:len(line)].split(" = ")[0] + "_vector_x"
                    vectorNameY = line[4:len(line)].split(" = ")[0] + "_vector_y"
                    vectorX = variableValue[8:len(variableValue) - 1].split(", ")[0]
                    vectorY = variableValue[8:len(variableValue) - 1].split(", ")[1]
                    compiliedLine = vectorNameX + " = " + vectorX + "\n" + vectorNameY + " = " + vectorY
                elif len(variableValue.split("(")) > 1:
                    compiliedLine = line[4:len(line)].split(" = ")[0] + " = " + convertFunction(variableValue)
                else:
                    compiliedLine = line[4:len(line)]
                variables[compiliedLine.split(" = ")[0]] = ""
            elif line[:2] == "if" or line[:5] == "while" or line[:3] == "for":
                if len(ifLevels) > 0:
                    tabs = ifLevels[-1]
                    print(ifLevels)
                    ifLevels.pop()
                    print(ifLevels, len(ifLevels))
                    code.append(tabs + "end")
                ifLevels.append(tabs)
                ifSplit = line.split(" ")
                Condition = ""
                conditionArray = line[:-1].split(" ")
                for x in line[:-1].split(" "):
                    if not x == conditionArray[0]:
                        if x == conditionArray[len(conditionArray) - 1]:
                            Condition = Condition + x
                        else:
                            Condition = Condition + x + " "
                keyMapping = {
                    "ui_up": "Up",
                    "ui_down": "Down",
                    "ui_right": "Right",
                    "ui_left": "Left",
                    "ui_accept": "Select"
                }
                if ifSplit[1][:5] == "Input":
                    pressType = ""
                    if ifSplit[1].split("(")[0] == "Input.is_action_pressed":
                        pressType = "Keys.held."
                    elif ifSplit[1].split("(")[0] == "Input.is_action_just_pressed":
                        pressType = "Keys.newPress."
                    elif ifSplit[1].split("(")[0] == "Input.is_action_just_released":
                        pressType = "Keys.released."
                    else:
                        pressType = "Keys.held."
                    keyType = ""
                    if ifSplit[1].split("(")[1][1:-3] in keyMapping:
                        keyType = keyMapping[ifSplit[1].split("(")[1][1:-3]]
                    else:
                        keyType = "A"
                    Condition = pressType + keyType
                reconstructedCondition = ""
                for x in Condition.split(" "):
                    if len(x.split("(")) > 1:
                        reconstructedCondition = reconstructedCondition + convertFunction(x) + " "
                    else:
                        reconstructedCondition = reconstructedCondition + x + " "
                    
                    if x == Condition.split(" ")[len(Condition.split(" ")) - 1]:
                        reconstructedCondition = reconstructedCondition[:-1]
                if line[:2] == "if":
                    compiliedLine = "if " + reconstructedCondition + " then"
                elif line[:3] == "for":
                    compiliedLine = "for " + reconstructedCondition + " do"
                else:
                    compiliedLine = "while " + reconstructedCondition + " do"
            elif line[:5] == "else:":
                compiliedLine = "else"
            elif len(line.split("(")) > 1 and line.split("(")[0] + "(" + line.split("(")[1] == "await get_tree().create_timer":
                print(line.split("(")[0] + "(" + line.split("(")[1])
                compiliedLine = "sleep(" + str(float(line.split("(")[2].split(")")[0]) * 100) + ")"
            else:
                if len(line.split(" ")) > 1:
                    print(line)
                    print(variables)
                    if line.split(" ")[1] == "=" and line.split(" = ")[0] in variables:
                        compiliedLine = line
                if len(line.split("(")) > 1 and not len(line.split(".")) > 1 and line.split("(")[0] in functions:
                    compiliedLine = line
                

            print(compiliedLine)

            if newlines < oldNewLines and not len(ifLevels) == 0 and not compiliedLine[:2] == "if" and not compiliedLine[:5] == "while" and not compiliedLine[:4] == "else" and not compiliedLine[:3] == "for":
                tabs = ifLevels[-1]
                print(ifLevels)
                ifLevels.pop()
                print(ifLevels, len(ifLevels))
                code.append(tabs + "end")
            if line == "":
                for x in ifLevels:
                    tabs = ifLevels[-1]
                    print(ifLevels)
                    ifLevels.pop()
                    print(ifLevels, len(ifLevels))
                    code.append(tabs + "end")

            if isinstance(compiliedLine, str):
                if not compiliedLine == "":
                    tabs = ""
                    for t in range(0, newlines):
                        tabs = tabs + "\t"
                    code.append(tabs + compiliedLine)
            else:
                for x in compiliedLine:
                    if not x == "":
                        tabs = ""
                        for t in range(0, newlines):
                            tabs = tabs + "\t"
                        code.append(tabs + x)

            if newlines == 0 and declaringFunction and not line[:5] == "func ":
                declaringFunction = False
                code.append("end\n")
            if line == "" and declaringFunction and not line[:5] == "func ":
                declaringFunction = False
                code.append("end\n")
        return(code)

def compileGame(gameFolder, microLuaDirectory, Screen, convertMainScene, debugMode, extendScreen, compressionMinimum):
    script = []

    # Compile the Configurations and Main Scene into "fullJSON"
    fullJSON["Config"] = convertProject(gameFolder + "/project.godot")
    if convertMainScene:
        fullJSON["convertedScene"] = convertScene(gameFolder + "/" + fullJSON["Config"]["run/main_scene"][7:-1])

    resourcesJSON = json.loads(fullJSON["convertedScene"])["resources"]
    nodesJSON = json.loads(fullJSON["convertedScene"])["nodes"]

    for n in json.loads(fullJSON["convertedScene"])["nodes"]:
        if json.loads(fullJSON["convertedScene"])["nodes"][n]["parent"] == "root":
            rootNode = n
    if "script" in json.loads(fullJSON["convertedScene"])["nodes"][rootNode]:
        scriptPath = resourcesJSON[json.loads(fullJSON["convertedScene"])["nodes"][rootNode]["script"][13:-2]]["path"]
        script = convertScript(gameFolder + "/" + scriptPath[6:len(scriptPath)], json.loads(fullJSON["convertedScene"])["nodes"][rootNode], nodesJSON)
        print(script)
    
    resourcesCompilied = []
    nodePosXCompiled = []
    nodePosYCompiled = []
    nodesCompilied = []

    renamedResourceIDs = {}
    resourcePaths = {}
    resourceCount = 0

    nodeCount = 0

    # Get name of the game from fullJSON, get the path for the MicroLua Game
    gameName = str(fullJSON["Config"]["config/name"][1:-1])
    compiliedDirectory = microLuaDirectory + "/lua/scripts/" + gameName

    # Make a folder with the name of the game
    if not os.path.exists(compiliedDirectory):
        os.mkdir(compiliedDirectory)
    else:
        shutil.rmtree(compiliedDirectory)
        os.mkdir(compiliedDirectory)
    
    # Open/Create "index.lua" in the created folder
    resultFile = open(compiliedDirectory + "/index.lua", "w")

    shutil.copyfile("Installed/Icon.png", compiliedDirectory + "/Icon.png")
    selectedImage = Image.open("Installed/Icon.png")
    w, h = selectedImage.size
    aspectRatio = w / h
    newH = round(compressionMinimum / aspectRatio)
    resizedImage = selectedImage.resize((compressionMinimum, newH))
    resizedImage.save(compiliedDirectory + "/Icon.png")
    for r in resourcesJSON:
        print(str(resourcesJSON))
        print(r)
        path = str(resourcesJSON[r]["path"])
        if path[len(path) - 3:len(path)].lower() == "png" or path[len(path) - 3:len(path)].lower() == "svg":
            resourceCount = resourceCount + 1
            resourceName = "res" + str(resourceCount)
            renamedResourceIDs[r] = resourceName
            resourcesCompilied.append(resourceName + " = " + 'Image.load("' + path[6:len(path) - 3] + 'png", VRAM)\n')
            print(path[len(path) - 3:len(path)])
            if path[len(path) - 3:len(path)].lower() == "png":
                print(path[len(path) - 3:len(path)])
                resourcePaths[r] = compiliedDirectory + "/" + path[6:len(path)]
                pathFixed = ""
                print(resourcePaths[r].split("/"))
                for x in resourcePaths[r].split("/"):
                    print(len(resourcePaths[r].split("/")))
                    if not x == resourcePaths[r].split("/")[len(resourcePaths[r].split("/")) - 1]:
                        pathFixed = pathFixed + "/" + x
                checkingPath = ""
                for x in pathFixed[1:len(pathFixed)].split("/"):
                    checkingPath = checkingPath + x + "/"
                    print(checkingPath)
                    if not os.path.exists(checkingPath):
                        os.mkdir(checkingPath)
                shutil.copyfile(gameFolder + "/" + path[6:len(path)], resourcePaths[r])
                selectedImage = Image.open(gameFolder + "/" + path[6:len(path)])
                w, h = selectedImage.size
                aspectRatio = w / h
                newH = round(compressionMinimum / aspectRatio)
                resizedImage = selectedImage.resize((compressionMinimum, newH))
                resizedImage.save(resourcePaths[r])

    for o in nodesJSON:
        random.seed(nodesJSON[o]["name"])
        nodeCount = round(random.random() * 9999)
        nodeName = nodesJSON[o]["type"] + str(nodeCount)

        if "visible" in nodesJSON[o]:
            visible = nodesJSON[o]["visible"]
        else:
            visible = "true"

        nodeVisibleDisplay = nodeName + "_visible"
        nodePosXCompiled.append(nodeName + "_visible = " + str(visible) + "\n")
        nodesCompilied.append("if " + nodeVisibleDisplay + " then")
        tabs = "\t"

        if nodesJSON[o]["type"] == "Sprite2D":
            texture = nodesJSON[o]["texture"][13:-2]
            path = resourcesJSON[texture]["path"]
            if "position" in nodesJSON[o]:
                position = nodesJSON[o]["position"][8:-1]
            else:
                position = "0, 0"
            if "scale" in nodesJSON[o]:
                scale = nodesJSON[o]["scale"][8:-1]
            else:
                scale = "1, 1"
            if texture in resourcePaths:
                textureImage = Image.open(resourcePaths[texture])
                selectedImage = Image.open(gameFolder + "/" + path[6:len(path)])
            else:
                textureImage = Image.open(compiliedDirectory + "/" + "Icon.png")
                selectedImage = Image.open("Installed/Icon.png")
            ogw, ogh = selectedImage.size
            w, h = textureImage.size
            if not ogw < compressionMinimum + 1 and not ogh < compressionMinimum + 1:
                fixedw = float(ogw) / 3.4
                fixedh = float(ogh) / 3.4
            else:
                fixedw = ogw
                fixedh = ogh
            x = convertPosition(int(float(position.split(", ")[0])), 1152, 341, 42.5)
            y = convertPosition(int(float(position.split(", ")[1])), 648, 192, 0)
            if not fixedw == ogw:
                scalex = float(scale.split(", ")[0])
                scaley = float(scale.split(", ")[1])
            else:
                scalex = int(float(scale.split(", ")[0]))
                scaley = int(float(scale.split(", ")[1]))
            nodePosXCompiled.append(nodeName + "_position_x = " + str(x) + "\n")
            nodePosYCompiled.append(nodeName + "_position_y = " + str(y) + "\n")
            nodePosXCompiled.append(nodeName + "_scale_x = " + str(scalex) + "\n")
            nodePosYCompiled.append(nodeName + "_scale_y = " + str(scaley) + "\n")
            nodePosXDisplay = "(" + nodeName + "_position_x + camera_x) - " + str((fixedw * scalex) / 2)
            nodePosYDisplay = "(" + nodeName + "_position_y + camera_y) - " + str((fixedh * scaley) / 2)
            nodePosScaleXDisplay = nodeName + "_scale_x"
            nodePosScaleYDisplay = nodeName + "_scale_y"
            print(nodesJSON[o])
            nodesCompilied.append(tabs + "screen.blit(" + "SCREEN_DOWN" + ", " + nodePosXDisplay + ", " + nodePosYDisplay + ", " + renamedResourceIDs[texture] + ")")
            if extendScreen:
                nodesCompilied.append(tabs + "screen.blit(" + "SCREEN_UP" + ", " + nodePosXDisplay + " - 256, " + nodePosYDisplay + " - 192, " + renamedResourceIDs[texture] + ")")
            # nodesCompilied.append(tabs + "Image.scale(" + renamedResourceIDs[texture] + ", " + str(round(fixedw)) + " * " + str(nodePosScaleXDisplay) + ", " + str(round(fixedh))  + " * " + str(nodePosScaleYDisplay) + ")")
            nodesCompilied.append(tabs + "Image.scale(" + renamedResourceIDs[texture] + ", " + str(fixedw * scalex) + ", " + str(fixedh * scaley) + ")")
        if nodesJSON[o]["type"] == "Label":
            if "text" in nodesJSON[o]:
                text = nodesJSON[o]["text"]
            else:
                text = '""'
            if "offset_left" in nodesJSON[o]:
                positionx = nodesJSON[o]["offset_left"]
            else:
                positionx = "0"
            if "offset_top" in nodesJSON[o]:
                positiony = nodesJSON[o]["offset_top"]
            else:
                positiony = "0"
            x = convertPosition(int(float(positionx)), 1152, 341, 42.5)
            y = convertPosition(int(float(positiony)), 648, 192, 0)
            nodePosXCompiled.append(nodeName + "_position_x = " + str(x) + "\n")
            nodePosYCompiled.append(nodeName + "_position_y = " + str(y) + "\n")
            nodePosXCompiled.append(nodeName + "_text = " + str(text) + "\n")
            nodePosXDisplay = "(" + nodeName + "_position_x + camera_x)"
            nodePosYDisplay = "(" + nodeName + "_position_y + camera_y)"
            nodePosTextDisplay = nodeName + "_text"
            nodesCompilied.append(tabs + "screen.print(" + "SCREEN_DOWN" + ", " + nodePosXDisplay + ", " + nodePosYDisplay + ", " + nodePosTextDisplay + ", Color.new256(0, 0, 0))")
        nodesCompilied.append("end")

    # Put together the script
    with open(compiliedDirectory + "/index.lua", "a+") as f:
        if debugMode:
            f.writelines("Debug.ON()\n")
        else:
            f.writelines("Debug.OFF()\n")
        if Screen:
            f.writelines("screen.switch()\n\n")
        f.write("-- Resources\n")
        f.writelines(resourcesCompilied)
        f.write("\n-- Node Positions\n")
        f.writelines(nodePosXCompiled)
        f.writelines(nodePosYCompiled)
        f.write("\n-- Camera Position\n")
        f.write("camera_x = 0\n")
        f.write("camera_y = 0\n")
        f.write("\n-- Script Logic\n")
        if not script == []:
            for x in ["timer = Timer.new()\n", "timer:start()\n", "\n", "function sleep(a)\n", "\tsec = tonumber(timer:getTime() + a)\n", "\twhile (timer:getTime() < sec) do\n", "\tend\n", "end\n\n"]:
                f.write(x)
            for l in script:
                f.write(l + "\n")
        else:
            f.write("function _process(delta)\n")
            f.write("end\n")
        f.write("\n-- Basically _process()")
        f.write("\nwhile not Keys.newPress.Start do")
        f.write("\n\tControls.read()\n")
        f.write("\n\t-- Draw BG Color")
        f.write("\n\t" + "screen.drawFillRect(SCREEN_DOWN, 0, 0, 256, 192, Color.new256(76, 76, 76))" + "\n")
        if extendScreen:
            f.write("\n\t" + "screen.drawFillRect(SCREEN_UP, 0, 0, 256, 192, Color.new256(76, 76, 76))" + "\n")
        else:
            f.write("\n\t-- Draw Credit")
            f.write("\n\t" + 'screen.print(SCREEN_UP, 0, 0, "Compiled using Godot to DS, by Haynster")' + "\n")
        f.write("\n\t-- Do Script Logic\n")
        f.write("\t_process(0)\n")
        f.write("\n\t-- Draw Nodes and Render Screen\n")
        for n in nodesCompilied:
            f.write("\t" + n + "\n")
        f.write("\trender()\n")
        f.write("end\n")
    print("COMP SUCCESS")

microLuaDirectory = "MicroLua"
gameFolder = "GAME"
compileGame(gameFolder, microLuaDirectory, True, True, False, False, 64)