# Terraform configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# AWS Provider region. Change if needed
provider "aws" {
  region = "ap-southeast-2"
}


# Create a random string
resource "random_string" "random" {
  length  = 16
  special = false
  upper   = false
  lower   = true
  numeric = true
}

# Create the S3 bucket
resource "aws_s3_bucket" "example" {
  bucket = "iosbackups-backup-${random_string.random.result}" # Must be globally unique

  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}

# Output the bucket name for use in other tools
output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.example.bucket
}
# Enable versioning on the S3 bucket
resource "aws_s3_bucket_versioning" "backup_versioning" {
  bucket = aws_s3_bucket.example.id
  versioning_configuration {
    status = "Enabled"
  }
}