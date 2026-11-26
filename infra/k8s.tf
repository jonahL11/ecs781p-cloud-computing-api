data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.default.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.default.master_auth[0].cluster_ca_certificate)

  ignore_annotations = [
    "^autopilot\\.gke\\.io\\/.*",
    "^cloud\\.google\\.com\\/.*"
  ]
}

locals {
  app-container-base = "${var.deployment-region}-docker.pkg.dev/${var.project-id}/${var.app-repo-name}/${var.app-container-name}"
  app-container-full = "${local.app-container-base}:${var.app-container-tag}"
}

resource "kubernetes_ingress_v1" "default" {
  metadata {
    name = "${var.app-name}-ingress"
    annotations = {
      "kubernetes.io/ingress.global-static-ip-name" = google_compute_global_address.default.name
      "networking.gke.io/managed-certificates" = kubernetes_manifest.managed-certificate.manifest.metadata.name
      "networking.gke.io/v1beta1.FrontendConfig" = kubernetes_manifest.frontend-config.manifest.metadata.name
    }
  }
  spec {
    default_backend {
      service {
        name = kubernetes_service_v1.default.metadata[0].name
        port {
          number = 80
        }
      }
    }

    rule {
      http {
        path {
          backend {
            service {
              name = kubernetes_service_v1.default.metadata[0].name
              port {
                number = 80
              }
            }
          }

          path = "/*"
        }

      }
    }
  }
}

#
resource "kubernetes_manifest" "managed-certificate" {
  manifest = {
    apiVersion = "networking.gke.io/v1"
    kind       = "ManagedCertificate"
    metadata = {
      name      = "${var.app-name}-managed-certificate"
      namespace = "default"
    }
    spec = {
      domains = [var.domain-name]
    }
  }
}

# FrontendConfig redirect http to https!
resource "kubernetes_manifest" "frontend-config" {
  manifest = {
    apiVersion = "networking.gke.io/v1beta1"
    kind       = "FrontendConfig"
    metadata = {
      name      = "${var.app-name}-frontend-config"
      namespace = "default"
    }
    spec = {
      redirectToHttps = {
        enabled          = true
        responseCodeName = "MOVED_PERMANENTLY_DEFAULT" # 301 redirect
      }
    }
  }
}

# This defines a k8s workload, i.e. container(s) that is supposed to run
# deployment ensures enough/not too many replicas of pods run
resource "kubernetes_deployment_v1" "app" {
  metadata {
    name = "${var.app-name}-app-deployment"
  }

  spec {
    selector {
      match_labels = {
        app = "${var.app-name}-app"
      }
    }

    template {
      metadata {
        labels = {
          app = "${var.app-name}-app"
        }
      }

      spec {
        service_account_name = kubernetes_service_account_v1.app-ksa.metadata[0].name
        # Container 1 our app
        container {
          image = local.app-container-full
          name  = "${var.app-name}-app"

          port {
            container_port = 5050
            name           = "${var.app-name}-svc"
          }

          env {
            # because we use the proxy its like its the same localhost
            name  = "DB_HOST"
            value = "127.0.0.1"
          }
          env {
            name  = "DB_PORT"
            value = "3306"
          }
          env {
            name = "DB_USER"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.db-credentials.metadata[0].name
                key  = "username"
              }
            }
          }
          env {
            name = "DB_PASS"
            value_from {
              secret_key_ref {
                name = kubernetes_secret_v1.db-credentials.metadata[0].name
                key  = "password"
              }
            }
          }
          env {
            name = "DB_DIALECT"
            value = "mysql"
          }
          env {
            name = "DB_NAME"
            value = "main"
          }

          security_context {
            allow_privilege_escalation = false
            privileged                 = false
            read_only_root_filesystem  = false

            capabilities {
              add  = []
              drop = ["NET_RAW"]
            }

            seccomp_profile {
              type = "RuntimeDefault"
            }
          }

          liveness_probe {
            http_get {
              path = "/"
              port = "${var.app-name}-svc"

              http_header {
                name  = "X-Custom-Header"
                value = "Check"
              }
            }

            initial_delay_seconds = 3
            period_seconds        = 3
          }
        }
        # container 2 sql proxy as a sidecar
        container {
          name  = "cloud-sql-proxy"
          image = "gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.14.1"

          args = [
            "--structured-logs",
            "--port=5432",
            google_sql_database_instance.db_instance.connection_name
          ]

          security_context {
            run_as_non_root = true
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "200m"
              memory = "256Mi"
            }
          }
        }
        security_context {
          run_as_non_root            = true
        }

        # Toleration is currently required to prevent perpetual diff:
        # https://github.com/hashicorp/terraform-provider-kubernetes/pull/2380
        toleration {
          effect   = "NoSchedule"
          key      = "kubernetes.io/arch"
          operator = "Equal"
          value    = "amd64"
        }
      }
    }
  }
  depends_on = [
    google_service_account_iam_member.workload_identity_binding,
    google_project_iam_member.cloudsql_client
  ]
}

# This defines how our loadbalancer is configured
resource "kubernetes_service_v1" "default" {
  metadata {
    name = "${var.app-name}-app-node-port"
  }

  spec {
    selector = {
      app = kubernetes_deployment_v1.app.spec[0].selector[0].match_labels.app
    }

    ip_family_policy = "RequireDualStack"

    port {
      port        = 80
      target_port = kubernetes_deployment_v1.app.spec[0].template[0].spec[0].container[0].port[0].name
    }

    type = "NodePort"
  }

  depends_on = [time_sleep.wait_service_cleanup]
}

# Provide time for Service cleanup
resource "time_sleep" "wait_service_cleanup" {
  depends_on = [google_container_cluster.default]

  destroy_duration = "180s"
}
