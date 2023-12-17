import boto3
import botocore.exceptions
import shutil
import os
import json
import io


os.system("echo Clearing deployments folder so new deployment packages can be generated...")
# delete files from deployments folder so new ones can be generated
# Iterate over all files and subdirectories in the given folder
for root, dirs, files in os.walk("deployments", topdown=False):
    for file in files:
        file_path = os.path.join(root, file)
        # Remove file
        os.remove(file_path)
    for dir in dirs:
        dir_path = os.path.join(root, dir)
        # Remove directory
        os.rmdir(dir_path)
sitePackagesPath = r"Lib/site-packages"
pythonPackgesForDeployment = ["feedparser", "sgmllib.py", "six.py"]
parentFolder = os.getcwd()
jsonFile = json.load(open("aws_access.json"))[0]
awsAccessKey, awsSecretAccessKey = jsonFile["access_key"], jsonFile["secret_access_key"]
os.system("echo Establishing connection to AWS Lambda.")
client = boto3.client(service_name = "lambda",
                      region_name = "us-east-2",
                      aws_access_key_id = awsAccessKey, 
                      aws_secret_access_key = awsSecretAccessKey)
os.system("echo Successfully established connection to AWS Lambda.")
os.system("echo Beginning generation of deployment packages for RSS Feed Lambdas...")
for file in os.listdir(parentFolder): #iterate through files in the parent folder
    splitFileName = file.split(".") #split file name
    extension, fileNoPy = splitFileName[-1], splitFileName[0] #get thefile extension and the name of the file itself
    if extension == 'py' and fileNoPy not in ["deployPackages", "emailGenerator", "updateUserConfig", "sendEmail"]: #if the file is a python file and not this file go through deployment package creation process
        folderForDeployment = rf"deployments\{fileNoPy}" #generate the folder in the deployments folder
        fileName = rf"{parentFolder}/{file}" #get the full file path that we are going to move
        fileForDeployment = rf"{folderForDeployment}/lambda_function.py" #generate the file name with the file path leading to deployments folder
        os.mkdir(folderForDeployment) #create the folder for the deployment package
        shutil.copy(fileName, fileForDeployment) #copy the python file from this folder to the deployment folder
        for pythonPackage in pythonPackgesForDeployment: #iterate through the python packages to include the deployment package
            currentLocation = rf"{parentFolder}/{sitePackagesPath}/{pythonPackage}" #generate the current location of the python package
            deploymentLocation = rf"{parentFolder}/{folderForDeployment}/{pythonPackage}" #generate the location of the deployment package
            if pythonPackage.split(".")[-1] != "py": #if the python package is a folder
                shutil.copytree(currentLocation, deploymentLocation) #run the copy function that applies to folders
            else: #if the python package is just a python file
                shutil.copy(currentLocation, deploymentLocation) #run the copy function that applies to files
        fileCount = len(os.listdir(folderForDeployment)) #get the number of files/folders in the deployment folder
        if(fileCount == 4): #if there are 4 folders/files (this is the amount there should be), this acts as a check to ensure everything got copied over
            shutil.make_archive(folderForDeployment, 'zip', folderForDeployment) #convert the deployment folder to a zip file for transfer to AWS Lambda
            os.system(f"echo Completed deployment pacakge for: {fileNoPy}.") #print message saying that the deployment package was created successfully
        else:
            Exception(f"There was an error creating the following package: {fileNoPy}.") #if the file count isn't correct, throw an error saying there was an issue with generating the deployment package
os.system("echo Beginning generation of deployment package for email generation lambda...")
python_packages_for_email_script = ["boto3", "botocore", "bs4", "sgmllib.py", "six.py"]
email_file_for_deployment = rf"{parentFolder}/emailGenerator.py" #get the full file path that we are going to move
folder_for_email_generator_deployment = rf"{parentFolder}/deployments/emailGenerator"
email_generation_script_for_deployment = rf"{folder_for_email_generator_deployment}/lambda_function.py" #generate the file name with the file path leading to deployments folder
os.mkdir(folder_for_email_generator_deployment) #create the folder for the deployment package
shutil.copy(email_file_for_deployment, email_generation_script_for_deployment) #copy the python file from this folder to the deployment folder
for email_package in python_packages_for_email_script:
    current_email_python_package_location = rf"{parentFolder}/{sitePackagesPath}/{email_package}" #generate the current location of the python package
    deployment_email_python_package_location = rf"{folder_for_email_generator_deployment}/{email_package}" #generate the location of the deployment package
    if email_package.split(".")[-1] != "py": #if the python package is a folder
        shutil.copytree(current_email_python_package_location, deployment_email_python_package_location) #run the copy function that applies to folders
    else: #if the python package is just a python file
        shutil.copy(current_email_python_package_location, deployment_email_python_package_location)
    file_count = len(os.listdir(folder_for_email_generator_deployment)) #get the number of files/folders in the deployment folder
    if(file_count == 6): #if there are 4 folders/files (this is the amount there should be), this acts as a check to ensure everything got copied over
        shutil.make_archive(folder_for_email_generator_deployment, 'zip', folder_for_email_generator_deployment) #convert the deployment folder to a zip file for transfer to AWS Lambda
        os.system(f"echo Completed deployment pacakge for: emailGenerator.") #print message saying that the deployment package was created successfully
    else:
        Exception(f"There was an error creating the following package: emailGenerator.")
os.system("echo Beginning upload of deployment packages to AWS Lambda...")
deploymentPackages = []
for file in os.listdir(rf"{parentFolder}/deployments"):
    fileSplit = file.split(".")
    fullFilePath = f"{parentFolder}/deployments/{file}"
    file_name_only = fileSplit[0]
    if(file_name_only != 'emailGenerator'):
        function_name = f"get{file_name_only}Feed"
    else:
        function_name = file_name_only
    if fileSplit[-1] == "zip":
        buffer = io.BytesIO() #have to store the zip file as a buffer object to upload to AWS Lambda via API
        with open(fullFilePath, 'rb') as existing_zip_file:
            buffer.write(existing_zip_file.read())
        buffer.seek(0)
        try:
            response = client.delete_function(
                FunctionName=function_name, #delete the old version so we can add the new one
            )
            os.system(f"echo Deleted older version of {file_name_only} already in AWS Lambda.")
        except client.exceptions.ResourceNotFoundException:
            pass
        response = client.create_function(
            FunctionName = function_name,
            Runtime = "python3.9",
            Role = "arn:aws:iam::159535920112:role/lambda-newsletter-role", #created in AWS IAM console
            Handler = "lambda_function.lambda_handler", #this function name must be included in the main python file
            Code = {"ZipFile": buffer.read()},
            Timeout = 30
        )
        responseStatusCode = response["ResponseMetadata"]["HTTPStatusCode"]
        if responseStatusCode == 200 or responseStatusCode == 201:
            os.system(f"echo Successfully uploaded: {file_name_only} to AWS Lambda.")
        else:
            Exception(f"There was an error in uploading {file_name_only} to AWS Lambda.")