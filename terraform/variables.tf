variable "aws_profile" {
  description = "AWS profile to use for authentication."
  type        = string
  default     = "default"
}

variable "aws_region" {
  description = "AWS region to deploy resources."
  type        = string
  default     = "eu-north-1"
}

variable "ec2_key_name" {
  description = "Name of the EC2 Key Pair for SSH access to the instance."
  type        = string
  # No default - Set by in a terraform.tfvars file. Avoid silent EC2 with no SSH access.
}

variable "iam_instance_profile_name" {
  description = "Name of the IAM instance profile to attach to the EC2 instance."
  type        = string
  default     = "" # Allows to be overridden from a tfvars file. Skip attaching profile if not needed.
}

variable "ssh_allowed_ips" {
  description = "List of CIDRs allowed for SSH access"
  type        = list(string)
}

