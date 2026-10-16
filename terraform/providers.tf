provider "aws" {
  region = var.aws_region

  # credentials come from the environment / ~/.aws, never from this repo
  default_tags {
    tags = local.tags
  }
}
