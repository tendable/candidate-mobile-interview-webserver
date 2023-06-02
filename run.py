import sys
sys.path.append('./site-packages/')

from flask import Flask
from flask import jsonify
from flask import request
app = Flask(__name__)

import json

import os, random


#########
# Utils #
#########

def listdir_nohidden(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            yield f

def dataset():
    with open("dataset/areas.json") as areasFile, open("dataset/category_names.json") as categoryNamesFile, open("dataset/inspection_types.json") as inspectionTypesFile, open("dataset/questions.json") as questionsFile:
        return {
            "areas": json.load(areasFile)["areas"],
            "categoryNames": json.load(categoryNamesFile)["categoryNames"],
            "inspectionTypes": json.load(inspectionTypesFile)["inspectionTypes"],
            "questions": json.load(questionsFile)["questions"]
        }

def generate_random_inspection(id):
    data = dataset()

    numberOfCategories = random.randint(1, 4)
    categories = []
    for categoryIndex in range(numberOfCategories):
        questions = []
        numberOfQuestions = random.randint(1, 3)
        for questionIndex in range(numberOfQuestions):
            questions.append(random.choice(data["questions"]))

        categories.append(
            {
                "id": categoryIndex,
                "name": random.choice(data["categoryNames"]),
                "questions": questions
            }
        )

    return {
        "inspection": {
            "id": id,
            "inspectionType": random.choice(data["inspectionTypes"]),
            "area": random.choice(data["areas"]),
            "survey": {
                "categories": categories
            }
        }
    }

def random_inspection_file():
    path = "./inspections"
    fileName =  random.choice([x for x in listdir_nohidden(path) if os.path.isfile(os.path.join(path, x))])
    return path + "/" + fileName

def inspection_file(inspectionId):
    path = "./inspections/inspection" + str(inspectionId) + ".json"
    return path

################
# Global State #
################

users = {}
globalInspectionCounter = 0

##########
# Routes #
##########

@app.route('/api/generate_random_inspections/<count>')
def generate_random_inspections(count):
    path = "./inspections"
    for index in range(int(count)):
        filename = "inspection" + str(index) + ".json"
        random_inspection = generate_random_inspection(index)
        os.makedirs(os.path.dirname(path + "/" + filename), exist_ok=True)
        with open(path + "/" + filename, 'w') as fp:
            json.dump(random_inspection, fp)
    return "Success"

@app.route('/api/random_inspection')
def random_inspection():
    try:
        randomInspectionFile = random_inspection_file()
    except Exception as error:
        errorJson = jsonify({"error":"Could not find any inspections to select from. Have you accessed /api/generate_random_inspections/10 first to generate 10 mock data inspections? (you only need to do this once)"})
        return errorJson, 404

    with open(randomInspectionFile) as json_file:
        data = json.load(json_file)
        return jsonify(data)

@app.route('/api/inspections/<inspectionId>', methods=['GET', 'DELETE'])
def inspection(inspectionId):
    if request.method == 'GET':
        inspectionFile = inspection_file(inspectionId)
        try:
            with open(inspectionFile) as json_file:
                data = json.load(json_file)
                return jsonify(data)
        except Exception as error:
            errorJson = jsonify({"error":str(error)})
            return errorJson, 404
    elif request.method == "DELETE":
        try:
            os.remove("./inspections/inspection" + inspectionId + ".json")
            return ""
        except Exception as error:
            errorJson = jsonify({"error":str(error)})
            return errorJson, 404

@app.route('/api/register', methods=['POST'])
def register():
    body = request.json
    if all (k in body for k in ("email","password")):
        if body["email"] not in users:
            users[body["email"]] = body["password"]
            return ""
        else:
            return jsonify({"error":"User already exists. Restart the webserver to clear all the users"}), 401
    else:
        return jsonify({"error":"Invalid body, make sure it contains the email and password keys"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    body = request.json
    if not all (k in body for k in ("email","password")):
        return jsonify({"error":"Invalid body, make sure it contains the email and password keys"}), 400

    if body["email"] in users and users[body["email"]] == body["password"]:
        return "", 200
    else:
        return jsonify({"error":"Invalid user or password"}), 401

@app.route('/api/inspections/start')
def startInspection():
    global globalInspectionCounter
    inspectionFile = "./inspection.json"
    try:
        with open(inspectionFile) as json_file:
            data = json.load(json_file)
            data["inspection"]["id"] = globalInspectionCounter
            globalInspectionCounter += 1
            return jsonify(data)
    except Exception as error:
        errorJson = jsonify({"error":str(error)})
        return errorJson, 404

@app.route('/api/inspections/submit', methods=['POST'])
def submitInspection():
    global globalInspectionCounter

    body = request.json
    inspectionId = body["inspection"]["id"]
    inspectionFile = "inspection" + str(inspectionId) + ".json"
    try:
        with open("./inspections/" + inspectionFile, 'w') as fp:
                json.dump(body, fp)
    except Exception as error:
        errorJson = jsonify({"error":str(error)})
        return errorJson, 500
    
    return ""

port = 5001
if len(sys.argv) > 1:
    port = int(sys.argv[1])
app.run(debug=True, port=port, ssl_context=None)