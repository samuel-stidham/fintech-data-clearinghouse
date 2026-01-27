variable "deployer_public_key" {
  description = "Public key for SSH access (from deployer_key.pub)"
  type        = string
}

variable "vest_client_public_key" {
  description = "Public key for the SFTP user (Vest)"
  type        = string
  # No default = Must be provided at runtime
}
