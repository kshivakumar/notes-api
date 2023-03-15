variable "instance_type" {
  type    = string
  default = "t3.nano"
}

variable "image_id" {
  type    = string
  default = "ami-079168d91e76481a6" # amazon linux
}

variable "ec2_key_name" {
  type    = string
  default = "aws_mac_apsouth2"
}

variable "vpc_region" {
  type    = string
  default = "ap-south-2"
}

variable "postgres_instance_type" {
  type    = string
  default = "db.t3.micro"
}

variable "postgres_storage_type" {
  type    = string
  default = "gp2"
}

variable "postgres_db_size" {
  type    = number
  default = 10 # in GB
}

variable "postgres_dbname" {
  type    = string
  default = "notes_api"
}

variable "postgres_username" {
  type    = string
  default = "postgres"
}

variable "postgres_password" {
  type    = string
  default = "postgres"
}

variable "django_secret_key" {
  type      = string
  sensitive = true
  default   = "django-insecure-slj(_efp!da@c#xf+7th@54@0%8_+a#cd-)2&cop%g3_amr-51"
}

variable "django_debug" {
  type    = bool
  default = false
}

variable "django_static_root" {
  type = string
  default = "/var/www/static/"
}

variable "gunicorn_port" {
  type    = number
  default = 8000 # can't use 80, ports below 1024 require superuser privileges
}
