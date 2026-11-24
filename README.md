# ecs781p-cloud-computing-api

## Infrastructure

Infra is setup using [Terraform](https://developer.hashicorp.com/terraform).
IaC helps in keeping setups homogeneous and reproducible.
The Google Cloud SDK `gcloud` is used for authentication and CLI interactions with infrastructure.

### Infrastructure Prerequisites
> [!WARNING]
> The following instructions and pre-requisites have only been tested on MacOs machines. 
Linux should work similarly. However Windows machines require different syntax for environment variables. 

- have `terraform` CLI installed ([Link](https://developer.hashicorp.com/terraform/install))
- have `gcloud` CLI installed ([Link](https://docs.cloud.google.com/sdk/docs/install-sdk?hl=en))
- have a GCP project setup and set as default project context in `gcloud`
  ```bash
  gcloud init 
  # OR
  gcloud auth login # for devices with browser
  export PROJECT_ID="<your-gcp-project-id>"
  gcloud config set project ${PROJECT_ID}
  ```
- have GCP artifact registry (AR) enabled, including an existing docker repo
  ```bash
  export GCP_REGION="<your-gcp-region>" #like europe-west2
  
  # Enable artifact registry in your project
  gcloud services enable artifactregistry.googleapis.com
  # Enable API for database interactions
  gcloud services enable sqladmin.googleapis.com
  
  # implements an authentication helper for image push 
  gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
  
  # create AR repo
  export REPO_NAME="<your-repo-name>"
  gcloud artifacts repositories create ${REPO_NAME} --repository-format=docker --location=${GCP_REGION} --description="<your-description>"
  ```
- have a docker image pushed to AR
  ```bash
  # Build image locally (must have same OS as deployment OS)
  export IMAGE_NAME="<your-app-name>"
  export IMAGE_TAG="<your-app-image-version>"
  
  docker build . --platform linux/amd64 --tag=${IMAGE_NAME}:${IMAGE_TAG}
  
  # Tag local image with AR compliant name
  docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${GCP_REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}
  
  # Push local image to remote AR
  docker push ${GCP_REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}
  ```
- make image pullable by project service account during deployment
  ```bash
  # project number can be retrieved with `gcloud projects list`
  gcloud artifacts repositories add-iam-policy-binding ${REPO_NAME} --location=${GCP_REGION} --project=${PROJECT_ID} --member="serviceAccount:<your-project-number>-compute@developer.gserviceaccount.com" --role="roles/artifactregistry.reader"
  ```

### Applying deployment

Now you have set up a project, enabled and set up the AR and pushed a container image to it.
The next step is deployment of the computational resources to run the app, using terraform.
1) First step is to duplicate and rename the `tfvars.example` file.
In here you configure basic, reusable information about the deployment.
You fill out the respective variables with their correct values.
When naming the new file like `*.auto.tfvars` terraform uses them implicitly.
Do not add secrets here and do not commit a filled out `*.tfvars` file.
2) Now duplicate `secret.tfvars.example`, enter the correct values, and remove the `.example` suffix. These files are **never ever** intended to commit!
3) Now you need to initialize the terraform project to download all providers.
   ```bash
   terraform init
   ```
4) Now you can create a deployment plan (when you suffixed the basic variables with `*auto.tfvars`)
    ```bash
   terraform plan -out plan.tfplan -var-file=secret.tfvars
    ```
5) Now apply the plan
    ```bash
   terraform apply "plan.tfplan"
    ```
6) If you want to delete deployed resources, you can destroy them via terraform
    ```bash
   terraform destroy -var-file=secret.tfvars
    ```