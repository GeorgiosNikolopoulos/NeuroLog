import json
from pathlib import Path
import shutil
from azureml.core import Workspace, ComputeTarget, Dataset
from azureml.data.data_reference import DataReference
from azureml.pipeline.core import PipelineData
from azureml.pipeline.steps import EstimatorStep
from azureml.train.estimator import Estimator
from azureml.pipeline.core import Pipeline
from azureml.core import Experiment

with open("ptgnn/authentication.json") as jsonFile:
    authData = json.load(jsonFile)["CPU"]

convertCorpusLocation = Path("../convertCorpusForML.py")
convertCorpusAzureLocation = Path("./convertCorpusForML.py")
shutil.copy(convertCorpusLocation, convertCorpusAzureLocation)

subID = authData["subID"]  # Get from Azure Portal; used for billing
resGroup = authData["resGroup"]  # Name for the resource group
wsName = authData["wsName"]  # Name for the workspace, which is the collection of compute clusters + experiments
computeName = authData["computeName"]  # Name for computer cluster

ws = Workspace.get(wsName, subscription_id=subID, resource_group=resGroup)
computeTarget = ComputeTarget(ws, computeName)
datastore = ws.get_default_datastore()

inputData = DataReference(
    datastore=datastore,
    data_reference_name="input_data",
    path_on_datastore="corpus/severities.json"
)
inputCorpus = DataReference(
    datastore=datastore,
    data_reference_name="input_corpus",
    path_on_datastore="corpus/"
)

output = PipelineData("outputs", datastore=datastore)
source_directory = "."

est = Estimator(source_directory=source_directory,
                compute_target=computeTarget,
                entry_script='convertCorpusForML.py',
                conda_packages=["pip"],
                pip_packages=["azureml-core", "tqdm", "numpy", "protobuf"],
                use_docker=True,
                use_gpu=False)

estStep = EstimatorStep(name="Estimator_Train",
                        estimator=est,
                        estimator_entry_script_arguments=[inputData, 0.8, 0.2, output, "--aml_folder", inputCorpus,
                                                          "-l", 10],
                        runconfig_pipeline_params=None,
                        inputs=[inputData, inputCorpus],
                        outputs=[output],
                        compute_target=computeTarget)

pipeline = Pipeline(workspace=ws, steps=[estStep])
run = Experiment(ws, 'Convert_Corpus').submit(pipeline)
run.wait_for_completion(show_output=True)
