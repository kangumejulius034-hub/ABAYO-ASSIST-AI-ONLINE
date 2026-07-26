import json
import os


def save_fault(station, fault, causes, checks):

    knowledge_path = os.path.join("knowledge", "faults.json")

    try:
        with open(knowledge_path, "r", encoding="utf-8") as file:
            faults = json.load(file)

    except:
        faults = []

    new_fault = {
        "station": station,
        "fault": fault,
        "possible_causes": causes,
        "checks": checks
    }

    faults.append(new_fault)

    with open(knowledge_path, "w", encoding="utf-8") as file:
        json.dump(faults, file, indent=4)

    return True