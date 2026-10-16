terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # the EKS module v20 line needs a 5.x provider
      version = ">= 5.95, < 6.0"
    }
  }

  # Local state is fine for a one person project. To share state, create the bucket first
  # and uncomment this (S3 native locking needs terraform >= 1.10).
  # backend "s3" {
  #   bucket       = "REPLACE_WITH_STATE_BUCKET"
  #   key          = "clinicdesk/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  #   encrypt      = true
  # }
}
