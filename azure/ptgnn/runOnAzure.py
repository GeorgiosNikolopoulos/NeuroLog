from collections import OrderedDict
import json

import argparse
from azureml.core import Workspace, Experiment, Datastore
from azureml.core.compute import ComputeTarget
from azureml.core.environment import Environment, DockerSection
from azureml.train.estimator import Estimator


def main():
    with open("authentication.json") as jsonFile:
        authData = json.load(jsonFile)[args.auth_cluster]

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
            (datapath_prefix + args.train_file_name, ""),
            (datapath_prefix + args.validate_file_name, ""),
            (datapath_prefix + args.test_file_name, ""),
            ("./model.pkl.gz", ""),
            ("--max-num-epochs", args.max_epochs),
            ("--aml", ""),
            ("--azure-info", "azureinfo.json"),
            ("--quiet", "")
        ]
    )
    # we are trying to predict statements
    if args.predicting_statement:
        script_params["--predicting-statement"] = ""

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
    exp = Experiment(workspace=ws, name=args.exp_name)
    run = exp.submit(config=est, tags=args.tags)
    print("Experiment Started. Remember you can exit out of this program but the experiment will still run on Azure!")
    # print("Portal URL: ", run.get_portal_url())
    run.wait_for_completion(show_output=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a training session on Azure.")
    parser.add_argument("auth_cluster", help="Which object to use from the JSON. Determines subscriptionID, workspace"
                                             "cluster, datastore etc.", type=str)

    parser.add_argument("exp_name", help="The name of the experiment on azure.", type=str)
    parser.add_argument("max_epochs", help="The maximum number of epochs the machine will run", type=str)
    parser.add_argument("train_file_name", help="The name of the training gz file. Pass the path to the json file",
                        type=str)
    parser.add_argument("validate_file_name", help="The name of the validation gz file. Pass the path to the json file",
                        type=str)
    parser.add_argument("test_file_name", help="The name of the test gz file. Pass the path to the json file", type=str)
    parser.add_argument("tags", help='A dictionary object with whatever info you want to add to the run as a tag. '
                                     'Please supply in the following format: {\"logs\":\"603\"}', type=json.loads)
    parser.add_argument("--predicting_statement", help="Set this if you are trying to predict statements instead of "
                                                       "severity", action="store_true")
    args = parser.parse_args()
    main()
