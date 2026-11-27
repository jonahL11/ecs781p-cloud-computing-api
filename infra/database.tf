terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.23.0"
    }
  }
}
resource "google_sql_database_instance" "db_instance" {
  project = var.project-id
  name             = "db-mysql-${var.project-id}"
  region           = var.deployment-region
  database_version = var.db-version
  //root_password    = var.db-password
  settings {
    tier = "db-f1-micro"
  }
  # set `deletion_protection` to true, will ensure that one cannot accidentally delete this instance by
  # use of Terraform whereas `deletion_protection_enabled` flag protects this instance at the GCP level.
  deletion_protection = false
}

# create explicit sub db from instance
resource "google_sql_database" "main" {
  project = var.project-id
  instance = google_sql_database_instance.db_instance.name
  name     = "main"
}

# add a db user with which the app can auth
resource "google_sql_user" "app-user" {
  project = var.project-id
  name     = "${var.app-name}-user"
  instance = google_sql_database_instance.db_instance.name
  password = var.db-password
}

# creates a service account to interact with cloud sql proxy sidecar
resource "google_service_account" "cloudsql_proxy_gsa" {
  project = var.project-id
  account_id   = "cloudsql-proxy-service-account"
  display_name = "cloudsql-proxy-service-account"
}

# gives the service acc roles to interact with cloudsql resources
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project-id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudsql_proxy_gsa.email}"
}

# bind k8s service acc to the gcp database service acc
resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.cloudsql_proxy_gsa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project-id}.svc.id.goog[default/my-app-ksa]"
}

resource "kubernetes_service_account_v1" "app-ksa" {
  metadata {
    name      = "${var.project-id}-kubernetes-service-acc"
    namespace = "default"
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.cloudsql_proxy_gsa.email
    }
  }
}
# make db password availale for kubernetes serrvice account
resource "kubernetes_secret_v1" "db-credentials" {
  metadata {
    name      = "kubernetes-secret-db-credentials"
    namespace = "default"
  }
  data = {
    username = google_sql_user.app-user.name
    password = var.db-password
    database = google_sql_database.main.name
  }
}