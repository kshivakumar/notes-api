data "http" "my_ip" {
  url = "https://checkip.amazonaws.com/"
}

provider "aws" {
  region = var.vpc_region
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.vpc_region}a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.vpc_region}b"
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "ec2" {
  name   = "ec2-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.my_ip.response_body)}/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "app_server" {
  ami           = var.image_id
  instance_type = var.instance_type
  key_name      = var.ec2_key_name

  vpc_security_group_ids = [aws_security_group.ec2.id]
  subnet_id              = aws_subnet.public.id

  user_data = base64encode(templatefile("${path.module}/setup.sh", {
    postgres_host     = aws_db_instance.postgres.address
    postgres_dbname   = aws_db_instance.postgres.db_name
    postgres_username = aws_db_instance.postgres.username
    postgres_password = aws_db_instance.postgres.password
    django_debug      = var.django_debug
    django_secret_key = var.django_secret_key
    django_static_root = var.django_static_root
    gunicorn_port     = var.gunicorn_port
  }))
}

resource "aws_security_group" "rds" {
  name   = "rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["${chomp(data.http.my_ip.response_body)}/32"]
  }
}

resource "aws_db_instance" "postgres" {
  identifier          = "app-database"
  engine              = "postgres"
  engine_version      = "14"
  instance_class      = var.postgres_instance_type
  storage_type        = var.postgres_storage_type
  allocated_storage   = var.postgres_db_size
  db_name             = var.postgres_dbname
  username            = var.postgres_username
  password            = var.postgres_password
  skip_final_snapshot = true

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.default.name

  publicly_accessible = true
}

resource "aws_db_subnet_group" "default" {
  name       = "main"
  subnet_ids = [aws_subnet.public.id, aws_subnet.private.id]
}

output "app_url" {
  value = "http://${aws_instance.app_server.public_ip}:${var.gunicorn_port}/api"
}

output "rds_public_access" {
  value = "PGPASSWORD=${var.postgres_password} psql -h ${aws_db_instance.postgres.address} -U ${var.postgres_username} -d ${var.postgres_dbname}"
}

