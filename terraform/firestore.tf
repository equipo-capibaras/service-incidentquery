# Enables the Firestore API for the project.
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"

  # Prevents the API from being disabled when the resource is destroyed.
  disable_on_destroy = false
}

# Grants the service account the "Datastore User" role on the project.
# This allows the service account (this microservice) to access the firestore database.
resource "google_project_iam_member" "firestore" {
  project = local.project_id
  role    = "roles/datastore.user"
  member  = google_service_account.service.member
}
