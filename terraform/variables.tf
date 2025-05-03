variable "ssh_allowed_ips" {
  description = "List of CIDRs allowed for SSH access"
  type        = list(string)
}

variable "instance_name" {
  description = "Value for the name tag for EC2 instance."
  type        = string
  default     = "gdd-server"
}

variable "ec2_instance_type" {
  description = ""
  type        = string
  default     = "t2.micro"
}
