import json
import shutil
from pathlib import Path

from azureml.core import Experiment
from azureml.core import Workspace, ComputeTarget
from azureml.train.estimator import Estimator

# Ger our configs
with open("ptgnn/authentication.json") as jsonFile:
    authData = json.load(jsonFile)["CPU"]

# Copy the convertCorpus script here. Done so we don't upload the corpus to Azure. (It's weird, I know. It works so
# don't question it)
convertCorpusLocation = Path("../convertCorpusForML.py")
convertCorpusAzureLocation = Path("./convertCorpusForML.py")
shutil.copy(convertCorpusLocation, convertCorpusAzureLocation)

# Grab the authentication data from the JSON file
subID = authData["subID"]  # Get from Azure Portal; used for billing
resGroup = authData["resGroup"]  # Name for the resource group
wsName = authData["wsName"]  # Name for the workspace, which is the collection of compute clusters + experiments
computeName = authData["computeName"]  # Name for computer cluster

# Get the workspace, the compute target and the datastore
ws = Workspace.get(wsName, subscription_id=subID, resource_group=resGroup)
computeTarget = ComputeTarget(ws, computeName)
datastore = ws.get_default_datastore()

# Download the entire corpus to the compute target. Save the DataReference obj here
# as_mount is also possible, but slows things down due to network opening of files
corpus_location = datastore.path("data/modified_corpus/").as_download()
output_location = "./"
# The files that will be uploaded for usage by our script (everything in the azure folder)
source_directory = "."

# params for the script
params = {
    "--corpus_location": corpus_location,
    "--output_folder": output_location,
    "--aml": "",
    "--training_percent": "0.8",
    "--validation_percent": "0.2",
    "-l": "300",
    "-c": ""
}
# Set up the estimator object. Note the inputs element, it tells azure that corpus_location in params
# will be a DataReference Object.
est = Estimator(source_directory=source_directory,
                compute_target=computeTarget,
                entry_script='convertCorpusForML.py',
                script_params=params,
                inputs=[corpus_location],
                conda_packages=["pip"],
                pip_packages=["azureml-core", "tqdm", "numpy", "protobuf"],
                use_docker=True,
                use_gpu=False)
# Start the experiment
run = Experiment(ws, 'Convert_Corpus').submit(config=est)
# remove the copy of convertCorpus (Remember, don't question this)
convertCorpusAzureLocation.unlink()
# print out the portral URL
print("Portal URL: ", run.get_portal_url())
# this will stream everything that the compute target does.
#run.wait_for_completion(show_output=True)
