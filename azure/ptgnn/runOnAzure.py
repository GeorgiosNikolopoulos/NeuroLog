from collections import OrderedDict
import json
from azureml.core import Workspace, Experiment, Datastore
from azureml.core.compute import ComputeTarget
from azureml.core.environment import Environment, DockerSection
from azureml.train.estimator import Estimator

with open("authentication.json") as jsonFile:
    authData = json.load(jsonFile)["GPU"]

# AzureML Subscription Details (get details from the Azure Portal)
subID = authData["subID"]  # Get from Azure Portal; used for billing
resGroup = authData["resGroup"]  # Name for the resource group
wsName = authData["wsName"]  # Name for the workspace, which is the collection of compute clusters + experiments
computeName = authData["computeName"]  # Name for computer cluster
### Get workspace and compute target
ws = Workspace.get(wsName, subscription_id=subID, resource_group=resGroup)
compute_target = ComputeTarget(ws, computeName)

# The path to the dataset. If using RichPath then this should be prefixed with azure://
# otherwise this is the location where the AzureML Datastore will be mounted
# datapath_prefix = "azure://example1234/data/"
# Set up by using the URL like above as well as a generated SAS key, placed into azureinfo.json
datapath_prefix = authData["dataPath"]
script_folder = "."
script_params = OrderedDict(
    [
        (datapath_prefix + "trainLogs.jsonl.gz", ""),
        (datapath_prefix + "testLogs.jsonl.gz", ""),
        (datapath_prefix + "validationLogs.jsonl.gz", ""),
        ("./model.pkl.gz", ""),
        ("--max-num-epochs", "100"),
        ("--aml", ""),
        ("--azure-info", "azureinfo.json"),
        ("--quiet", "")
    ]
)

with open("Dockerfile") as f:
    docker = DockerSection()
    docker.base_image = None
    docker.base_dockerfile = f.read()
    docker.enabled = True

environment = Environment(name="pytorchenv")
environment.docker = docker
environment.python.user_managed_dependencies = True

est = Estimator(
    source_directory=script_folder,
    script_params=script_params,
    compute_target=compute_target,
    entry_script="ptgnn/implementations/graph2seq/trainandtest.py",
    environment_definition=environment,
    use_docker=True,
)

### Submit the experiment
exp = Experiment(workspace=ws, name="NEUROLOG-Testing")
run = exp.submit(config=est)
print("Portal URL: ", run.get_portal_url())
run.wait_for_completion(show_output=True)
