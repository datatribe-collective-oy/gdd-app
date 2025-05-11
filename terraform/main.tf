provider "aws" {
  profile = "default"
  region  = "eu-north-1"
}


# Layer 1: Network (VPC, Subnet, Security Group)


resource "aws_vpc" "gdd_vpc" {
  cidr_block = "10.0.0.0/16"

  enable_dns_support = true
  enable_dns_hostnames = true

  tags = {
    Name    = "gdd-vpc"
    Project = "GDD-Timing-System"
  }
}

resource "aws_subnet" "gdd_public_subnet" {
  vpc_id                  = aws_vpc.gdd_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "eu-north-1a"
  map_public_ip_on_launch = true

  tags = {
    Name    = "gdd-public-subnet"
    Project = "GDD-Timing-System"
  }
}

resource "aws_internet_gateway" "gdd_igw" {
  vpc_id = aws_vpc.gdd_vpc.id
}

resource "aws_route_table" "gdd_route_table" {
  vpc_id = aws_vpc.gdd_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gdd_igw.id
  }
}

resource "aws_route_table_association" "gdd_rta" {
  subnet_id      = aws_subnet.gdd_public_subnet.id
  route_table_id = aws_route_table.gdd_route_table.id
}

resource "aws_security_group" "gdd_sg" {
  name_prefix = "gdd-sg-"
  vpc_id      = aws_vpc.gdd_vpc.id

ingress {
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
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



# Layer 2: Compute (EC2 Instance)


resource "aws_instance" "gdd_server" {
  ami                    = "ami-0dd574ef87b79ac6c"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.gdd_public_subnet.id
  security_groups        = [aws_security_group.gdd_sg.id]


  associate_public_ip_address = true

  iam_instance_profile = var.iam_instance_profile_name


  user_data = file("${path.module}/user_data/ec2-setup.sh")

  tags = {
    Name    = "gdd-server"
    Project = "GDD-Timing-System"
  }
}


# Layer 4: Data Storage (S3)


resource "aws_s3_bucket" "gdd_raw_data" {
  bucket        = "gdd-raw-weather-data"
  force_destroy = true # dev only 

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


# Outputs


output "gdd_server_public_ip" {
  value = aws_instance.gdd_server.public_ip
}

output "gdd_server_public_dns" {
  value = aws_instance.gdd_server.public_dns
}
