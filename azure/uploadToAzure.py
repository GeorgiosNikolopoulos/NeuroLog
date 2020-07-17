import json
from azureml.core import Workspace

# Uploads a directory to azure
def uploadToAzure(srcDir, destinationDir):
    with open("ptgnn/authentication.json") as jsonf:
        authData = json.load(jsonf)["GPU"]
    subID = authData["subID"]
    resGroup = authData["resGroup"]
    wsName = authData["wsName"]
    ws = Workspace.get(wsName, subscription_id=subID, resource_group=resGroup)
    datastore = ws.get_default_datastore()
    datastore.upload(src_dir=srcDir, target_path=destinationDir, overwrite=True, show_progress=True)

uploadToAzure(srcDir="../modified_corpus/", destinationDir="/data/modified_corpus")