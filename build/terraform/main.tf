terraform {
  backend "s3" {
    bucket = "vest-tf-state-samuel-stidham-001"
    key    = "prod/terraform.tfstate"
    region = "us-west-2"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"

  default_tags {
    tags = {
      CandidateId = "samuel-stidham-001"
      Project     = "fintech-data-clearinghouse"
    }
  }
}

# ---------------------------------------------------------
# Security Group
# ---------------------------------------------------------
resource "aws_security_group" "app_sg" {
  name        = "clearinghouse-sg"
  description = "Allow SSH, HTTP, and SFTP"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SFTP"
    from_port   = 2222
    to_port     = 2222
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------------------------------------------------------
# EC2 Instance
# ---------------------------------------------------------
resource "aws_key_pair" "deployer" {
  key_name   = "samuel-deployer-key"
  public_key = var.deployer_public_key
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.medium"

  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io docker-compose
              systemctl enable docker
              systemctl start docker
              usermod -aG docker ubuntu

              mkdir -p /home/ubuntu/sftp_keys
              echo "${var.vest_client_public_key}" > /home/ubuntu/sftp_keys/vest_user.pub
              chown -R ubuntu:ubuntu /home/ubuntu/sftp_keys
              chmod 644 /home/ubuntu/sftp_keys/vest_user.pub
              EOF

  tags = {
    Name = "Clearinghouse-Box"
  }
}
