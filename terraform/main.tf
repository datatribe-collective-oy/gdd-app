provider "aws" {
  profile = "default"
  region  = "eu-north-1"
}

# Layer 1: Public Network Access
resource "aws_security_group" "gdd_sg" {
  name_prefix = "gdd-sg-"

  ingress {
    from_port   = 443 # HTTPS
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22 # SSH
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_ips # allowed IPs defined
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = "GDD-Timing-System"
  }
}

# Layer 2 & 3: Application & ETL
resource "aws_instance" "gdd_server" {
  ami           = "ami-0dd574ef87b79ac6c" # amazon linux 2023
  instance_type = "t3.micro"

  user_data = file("${path.module}/user_data/ec2-docker.sh")


  tags = {
    Name    = "gdd-server"
    Project = "GDD-Timing-System"
  }
}


# Layer 4: Data Storage 
resource "aws_s3_bucket" "gdd_raw_data" {
  bucket        = "gdd-raw-weather-data"
  force_destroy = true # for dev only

  tags = {
    Project = "GDD-Timing-System"
  }
}

resource "aws_s3_bucket_public_access_block" "gdd_raw_data_block" {
  bucket = aws_s3_bucket.gdd_raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Prints IP and DNS values on CLI when applying terraform apply or terraform output.
output "gdd_server_public_ip" {
  value = aws_instance.gdd_server.public_ip
}

output "gdd_server_public_dns" {
  value = aws_instance.gdd_server.public_dns
}
