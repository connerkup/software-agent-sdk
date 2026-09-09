terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "main-project-482516"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "instance_name" {
  description = "Name of the Antigravity Orchestrator instance"
  type        = string
  default     = "agy-orchestrator-1"
}

variable "machine_type" {
  description = "Machine type for the instance (ARM Tau or Intel)"
  type        = string
  default     = "t2a-standard-4"
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_instance" "agy_orchestrator" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["antigravity", "openhands-harness", "mesh-node"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-arm64"
      size  = 60
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral external IP
    }
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  metadata = {
    enable-oslogin = "TRUE"
    startup-script = file("${path.module}/startup.sh")
  }

  lifecycle {
    create_before_destroy = true
  }
}

output "instance_name" {
  value = google_compute_instance.agy_orchestrator.name
}

output "instance_external_ip" {
  value = google_compute_instance.agy_orchestrator.network_interface[0].access_config[0].nat_ip
}
