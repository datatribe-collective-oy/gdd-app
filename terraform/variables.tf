variable "ssh_allowed_ips" {
  description = "List of CIDRs allowed for SSH access to the EC2 instance."
  type        = list(string)
}


variable "instance_name" {
  description = "Value for the Name tag applied to the EC2 instance."
  type        = string
  default     = "gdd-server"
}

variable "ec2_instance_type" {
  description = "EC2 instance type to use for the server."
  type        = string
  default     = "t3.micro"
}

variable "iam_instance_profile_name" {
  description = "Name of the existing IAM instance profile to attach to the EC2 instance."
  type        = string
  default     = "Airflow-instance-profile"
}


