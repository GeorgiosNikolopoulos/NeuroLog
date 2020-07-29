import json
import shutil
from pathlib import Path

import argparse
from azureml.core import Experiment, Datastore
from azureml.core import Workspace, ComputeTarget
from azureml.train.estimator import Estimator


def main():
    # Ger our configs
    with open("ptgnn/authentication.json") as jsonFile:
        authData = json.load(jsonFile)[args.auth_cluster]

    # Copy the convertCorpus script here. Done so we don't upload the corpus to Azure, or keep a copy of the script in here.
    # (It's weird, I know. It works and has a purpose though)
    convertCorpusLocation = Path("../convertCorpusForML.py")
    convertCorpusAzureLocation = Path("./convertCorpusForML.py")
    shutil.copy(convertCorpusLocation, convertCorpusAzureLocation)

    # Grab the authentication data from the JSON file
    subID = authData["subID"]  # Get from Azure Portal; used for billing
    resGroup = authData["resGroup"]  # Name for the resource group
    wsName = authData["wsName"]  # Name for the workspace, which is the collection of compute clusters + experiments
    computeName = authData["computeName"]  # Name for computer cluster
    datastoreName = authData["datastoreName"]

    # Get the workspace, the compute target and the datastore
    ws = Workspace.get(wsName, subscription_id=subID, resource_group=resGroup)
    computeTarget = ComputeTarget(ws, computeName)
    datastore = Datastore(ws, name=datastoreName)

    # Download the entire corpus to the compute target. Save the DataReference obj here
    # as_mount is also possible, but slows things down due to network opening of files
    corpus_location = datastore.path(args.aml_location).as_download()
    output_location = "./"
    # The files that will be uploaded for usage by our script (everything in the azure folder)
    source_directory = "."

    # params for the script
    params = {
        "--corpus_location": corpus_location,
        "--output_folder": output_location,
        "--aml": "",
        "--training_percent": args.training_percent,
        "--validation_percent": args.validation_percent,
        "-c": ""
    }
    if args.log_num is not None:
        params["-l"] = args.log_num
        tags = {
            "logs": str(args.log_num)
        }
    else:
        tags = {
            "logs": "MAX"
        }
    if args.statement_generation:
        params["-s"] = ""
        tags["generationType"] = "Statement"
    else:
        tags["generationType"] = "Severity"
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
    run = Experiment(ws, args.exp_name).submit(config=est, tags=tags)
    # remove the copy of convertCorpus (Remember, don't question this)
    convertCorpusAzureLocation.unlink()
    # print out the portral URL
    # print("Portal URL: ", run.get_portal_url())
    # this will stream everything that the compute target does.
    print("Experiment Started. Remember you can exit out of this program but the experiment will still run on Azure!")
    run.wait_for_completion(show_output=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert the corpus to plug into ML, now on the cloud!")
    parser.add_argument("auth_cluster", help="Which object to use from the JSON. Determines subscriptionID, workspace"
                                             "cluster, datastore etc.", type=str)
    parser.add_argument("aml_location", help="The location of the modified_corpus within the datastore. Ex. data/"
                                             "modified_corpus/", type=str)
    parser.add_argument("exp_name", help="The name of the experiment on azure.", type=str)
    parser.add_argument("training_percent", help="The percent of data that will be the training data (ex. 0.8). The "
                                                 "other 20 will be testing data",
                        type=str)
    parser.add_argument("validation_percent", help="The percent of the TRAINING data that will be the validation set"
                                                   "(ex. a 0.8 0.2 will take 20%% of the TRAINING set, which is 80%% of "
                                                   "the whole data)",
                        type=str)
    parser.add_argument("-l", "--log_num", help="Number of logs to use from the entire dataset. Omit to run all",
                        type=int)
    parser.add_argument("-s", "--statement_generation", help="If set, the output data is the training data for logging"
                                                             "statement prediction, if false then it's for logging severity"
                                                             "prediction", action="store_true")
    args = parser.parse_args()
    main()
