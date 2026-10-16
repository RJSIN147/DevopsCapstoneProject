variable "aws_region" {
  description = "AWS region for everything"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Used as a prefix for resource names and tags"
  type        = string
  default     = "clinicdesk"
}

variable "environment" {
  description = "dev / staging / prod"
  type        = string
  default     = "dev"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "clinicdesk-eks"
}

variable "kubernetes_version" {
  description = "EKS control plane version. Keep it on a version in standard support, extended support costs extra"
  type        = string
  default     = "1.34"
}

variable "vpc_cidr" {
  description = "CIDR for the VPC"
  type        = string
  default     = "10.30.0.0/16"
}

variable "az_count" {
  description = "How many availability zones to spread subnets over (EKS needs at least 2)"
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count must be 2 or 3."
  }
}

variable "node_instance_types" {
  description = "Instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_capacity_type" {
  description = "ON_DEMAND or SPOT. SPOT is a lot cheaper for a demo cluster"
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_capacity_type)
    error_message = "node_capacity_type must be ON_DEMAND or SPOT."
  }
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "Who can reach the public EKS API endpoint. Lock this to your own IP if you can"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
