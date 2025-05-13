provider "aws" {
  profile = var.aws_profile 
  region  = var.aws_region  
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" 
    }
  }
}



# Layer 1: Network (VPC, Subnet, Security Group)
resource "aws_vpc" "gdd_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name    = "gdd-vpc"
    Project = "GDD-Timing-System"
  }
}

resource "aws_subnet" "gdd_public_subnet" {
  vpc_id                  = aws_vpc.gdd_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a" 
  map_public_ip_on_launch = true

  tags = {
    Name    = "gdd-public-subnet"
    Project = "GDD-Timing-System"
  }
}

resource "aws_internet_gateway" "gdd_igw" {
  vpc_id = aws_vpc.gdd_vpc.id

  tags = {
    Name    = "gdd-igw"
    Project = "GDD-Timing-System"
  }
}

resource "aws_route_table" "gdd_route_table" {
  vpc_id = aws_vpc.gdd_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gdd_igw.id
  }

  tags = {
    Name    = "gdd-public-route-table"
    Project = "GDD-Timing-System"
  }
}

resource "aws_route_table_association" "gdd_rta" {
  subnet_id      = aws_subnet.gdd_public_subnet.id
  route_table_id = aws_route_table.gdd_route_table.id
}

resource "aws_security_group" "gdd_sg" {
  name_prefix = "gdd-sg-"
  description = "Allow HTTP, HTTPS, and SSH"
  vpc_id      = aws_vpc.gdd_vpc.id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_ips 
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # Allows all outbound traffic
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "gdd-server-sg"
    Project = "GDD-Timing-System"
  }
}

# Layer 2: Compute (EC2 Instance)
resource "aws_instance" "gdd_server" {
  ami                         = "ami-0dd574ef87b79ac6c"
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.gdd_public_subnet.id
  vpc_security_group_ids      = [aws_security_group.gdd_sg.id]
  associate_public_ip_address = true
  key_name                    = aws_key_pair.gdd_key.key_name


  iam_instance_profile = var.iam_instance_profile_name 

  user_data = templatefile("${path.module}/user_data/ec2-setup.tpl", {})

  user_data_replace_on_change = true # re-run on changes

  tags = {
    Name    = "gdd-server"
    Project = "GDD-Timing-System"
  }

  depends_on = [aws_internet_gateway.gdd_igw]
}

resource "aws_key_pair" "gdd_key" {
  key_name   = var.ec2_key_name
  public_key = file("~/.ssh/gdd_key.pub")
}

# Layer 4: Data Storage (S3)
resource "aws_s3_bucket" "gdd_raw_data" {
  bucket        = "gdd-raw-weather-data" # bucket name
  force_destroy = true # dev only - This will delete all objects in the bucket on destroy.

  tags = {
    Project = "GDD-Timing-System"
  }
}



resource "aws_s3_bucket_public_access_block" "gdd_raw_data_block" {
  bucket                  = aws_s3_bucket.gdd_raw_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Outputs
output "gdd_server_public_ip" {
  description = "Public IP address of the GDD server."
  value       = aws_instance.gdd_server.public_ip
}

output "gdd_server_public_dns" {
  description = "Public DNS name of the GDD server."
  value       = aws_instance.gdd_server.public_dns
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for raw data."
  value       = aws_s3_bucket.gdd_raw_data.bucket
}

output "selected_ami_id" {
  description = "The AMI ID being used for the EC2 instance."
  value       = aws_instance.gdd_server.ami
}