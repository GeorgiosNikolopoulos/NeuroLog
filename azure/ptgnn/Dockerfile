FROM mcr.microsoft.com/azureml/base-gpu:openmpi3.1.2-cuda10.1-cudnn7-ubuntu18.04

RUN python3 -m pip install --upgrade --no-cache-dir torch==1.5.1+cu101 torchvision==0.6.1+cu101 -f https://download.pytorch.org/whl/torch_stable.html
RUN python3 -m pip install --upgrade --no-cache-dir numpy scipy docopt dpu-utils more-itertools typing_extensions sentencepiece azureml-sdk pyyaml dill jellyfish
RUN python3 -m pip install --upgrade --no-cache-dir pip install torch-scatter==latest+cu101 -f https://pytorch-geometric.com/whl/torch-1.5.0.html
RUN export FORCE_CUDA=1