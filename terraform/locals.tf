locals {
  service_name = "incidentquery"
  database_name = "incident"
  project_id = var.gcp_project_id
  region = var.gcp_region
  domain = var.domain
}
