variable "instance_type" {
  type    = string
}

variable "image_id" {
  type    = string  # only amazon linux supported
}

variable "ec2_key_name" {
  type    = string
}

variable "vpc_region" {
  type    = string
}

variable "postgres_instance_type" {
  type    = string
}

variable "postgres_storage_type" {
  type    = string
}

variable "postgres_db_size" {
  type    = number
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
