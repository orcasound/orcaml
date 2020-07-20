# convenience script to download, unzip test/train data from the podcast data archive
# combine the train data and test data into a different dataset
import argparse
import os
import sys
import subprocess
import shutil
import gzip
import tarfile

def print_help():
    """

    """

    print("Please provide one or more of --test_data_download_location or --train_data_download_location")

def aws_download(s3_path, local_dir):
    command = "aws --no-sign-request s3 cp " + s3_path + " " + local_dir
    os.system(command)

    filename = os.path.basename(s3_path)
    full_path_to_filename = os.path.join(local_dir, filename)
    if not os.path.exists(full_path_to_filename):
        raise RuntimeError("{} does not exist".format(full_path_to_filename))
    return full_path_to_filename

def unzip_and_extract(test_data_download_location, local_download_location):
    # unzip file to folder
    # delete zip file after extraction
    extracted_folder_name = os.path.basename(local_download_location).split(".tar.gz")[0]
    extracted_folder_path = os.path.join(test_data_download_location, extracted_folder_name)
    if local_download_location.endswith("tar.gz"):
        tar = tarfile.open(local_download_location, "r:gz")
        tar.extractall(path=extracted_folder_path)
        tar.close()

    os.remove(local_download_location)
    return extracted_folder_path

def download_unzip_and_combine(test_dataset_paths, test_data_download_location, is_test = True):
    """

    """

    if os.path.exists(test_data_download_location):
        shutil.rmtree(test_data_download_location)
    os.mkdir(test_data_download_location)

    local_extracted_locations = []
    for test_data in test_dataset_paths:
        local_download_location = aws_download(test_data, test_data_download_location)
        local_extracted_location = unzip_and_extract(test_data_download_location, local_download_location)
        local_extracted_locations.append(local_extracted_location)

    # create a wav directory
    wav_dir = os.path.join(test_data_download_location, "wav")
    os.mkdir(wav_dir)

    if is_test:
        tsv_file = os.path.join(test_data_download_location, "test.tsv")
    else:
        tsv_file = os.path.join(test_data_download_location, "train.tsv")
    with open(tsv_file, "w") as outfile:
        for extracted_location in local_extracted_locations:
            inner_folder = os.listdir(extracted_location)[0]
            sub_wav_dir = os.path.join(extracted_location, inner_folder, "wav")
            for filename in os.listdir(sub_wav_dir):
                full_filename_path = os.path.join(sub_wav_dir, filename)
                # copy all wav files from sub_wav_dir to wav_dir
                shutil.copy(full_filename_path, wav_dir)
            
            if is_test:
                sub_test_tsv = os.path.join(extracted_location, inner_folder, "test.tsv")
            else:
                sub_test_tsv = os.path.join(extracted_location, inner_folder, "train.tsv")
            with open(sub_test_tsv, "r") as infile:
                outfile.write(infile.read())

            # delete extracted location
            shutil.rmtree(extracted_location)

    return test_data_download_location

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and combine dataset")
    parser.add_argument("--test_data_download_location")
    parser.add_argument("--train_data_download_location")
    args = parser.parse_args()

    # 
    if args.test_data_download_location is None and args.train_data_download_location is None:
        print_help()
        sys.exit(1)
    
    test_dataset_paths = [
        "s3://acoustic-sandbox/labeled-data/detection/test/OS_SVeirs_07_05_2019_08_24_00.tar.gz",
        "s3://acoustic-sandbox/labeled-data/detection/test/OrcasoundLab09272017_Test.tar.gz"
    ]
    if args.test_data_download_location:
        final_path = download_unzip_and_combine(test_dataset_paths, args.test_data_download_location)
        print("Test data extracted to {}".format(final_path))

    
    train_dataset_paths = [
        "s3://acoustic-sandbox/labeled-data/detection/train/WHOIS09222019_PodCastRound1.tar.gz",
        "s3://acoustic-sandbox/labeled-data/detection/train/OrcasoundLab07052019_PodCastRound2.tar.gz",
        "s3://acoustic-sandbox/labeled-data/detection/train/OrcasoundLab09272017_PodCastRound3.tar.gz"
    ]
    if args.train_data_download_location:
        final_path = download_unzip_and_combine(train_dataset_paths, args.train_data_download_location, False)
        print("Train data extracted to {}".format(final_path))
    
