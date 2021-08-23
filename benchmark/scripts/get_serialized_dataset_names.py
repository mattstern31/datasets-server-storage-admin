import typer
from datasets import list_datasets
from serialize import serialize_dataset_name

# import os
# import shutil



def main(filename: str):
    dataset_names = list_datasets(with_community_datasets=True)
    # replace '/' in namespaced dataset names
    serialized_dataset_names = [
        serialize_dataset_name(dataset_name) for dataset_name in dataset_names
    ]
    # # current subdirectories
    # dir_list = next(os.walk(path))[1]
    # # to add
    # for dataset in safe_datasets:
    #     if dataset not in dir_list:
    #         os.mkdir(os.path.join(path, dataset))
    # # to remove
    # for dataset in dir_list:
    #     if dataset not in safe_datasets:
    #         shutil.rmtree(os.path.join(path, dataset))
    with open(filename, "w") as f:
        for serialized_dataset_name in serialized_dataset_names:
            f.write("%s\n" % serialized_dataset_name)


if __name__ == "__main__":
    typer.run(main)