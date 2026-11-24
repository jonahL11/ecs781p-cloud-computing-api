// General Information
variable "project-id"{
  type = string
  description = "The GCP project ID in which the resources are deployed into"
  sensitive = false
}

variable "deployment-region" {
  type = string
  description = "The GCP region this single-region setup is deployed in"
  sensitive = false
}

// Database Information
variable "db-password" {
  description = "root Db password, must be secure! Set in environment variables"
  type        = string
  sensitive   = true
}

variable "db-version" {
  type = string
  default = "MYSQL_8_4_11"
  description = "Pinning the DB version including type and version. TYPE_XX_XX_XX like MYSQL_8_0_26"
  sensitive = false
}

// App/k8s workload Information
variable "app-name" {
  type = string
  description = "Name for app used for naming GCP resources"
  sensitive = false
}

variable "app-repo-name" {
  type = string
  description = "Docker repo name in artifact registry for app"
  sensitive = false
}

variable "app-container-name" {
  type = string
  description = "Image name in artifact registry"
  sensitive = false
}

variable "app-container-tag" {
  type = string
  description = "Version/tag of container version like 'latest' or 'v1'"
  sensitive = false
}

variable "domain-name" {
  type = string
  description = "Domain under which the app is supposed to be available. Needed for SSL cert"
  sensitive = false
}