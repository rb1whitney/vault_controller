# EC2 / GCE Virtual Machine Vault Integration

This example demonstrates how to pass the new unified `VAULT_AUTH_*` environment variables to a virtual machine (AWS EC2 or GCP GCE) via `user_data` (cloud-init), enabling applications on the VM to authenticate natively with Vault.

## AWS EC2 Example

### 1. External Infrastructure (Terraform)
```hcl
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

resource "aws_instance" "vault_worker" {
  ami                  = data.aws_ami.amazon_linux_2023.id
  instance_type        = "t3.micro"
  iam_instance_profile = aws_iam_instance_profile.worker_profile.name
  subnet_id            = aws_subnet.private_app.id

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # Enforce IMDSv2
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted   = true
    kms_key_id  = aws_kms_key.ebs_key.arn
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              echo "export VAULT_AUTH_TYPE=aws" >> /etc/profile.d/vault.sh
              echo "export VAULT_AUTH_PRINCIPAL=${aws_iam_role.worker_role.name}" >> /etc/profile.d/vault.sh
              EOF
}

# The AWS Auth Strategy will automatically use the instance's IAM metadata 
# to generate the signed request to Vault.
```

### 2. Internal Vault Configuration (YAML Payload)
**Example Payload (`example_vault/admin/_auth_methods.yaml`)**:
```yaml
api_paths:
- api_path: v1/auth/aws/role/${aws_iam_role.worker_role.name}
  api_action: post
  api_payload:
    auth_type: iam
    bound_iam_principal_arn: "arn:aws:iam::123456789012:role/worker_profile"
    policies: "automation-policy"
    max_ttl: "1h"
```

---

## GCP GCE Example

### 1. External Infrastructure (Terraform)
```hcl
resource "google_compute_instance" "vault_worker" {
  name         = "vault-worker-vm"
  machine_type = "e2-micro"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.private_app.self_link
  }

  service_account {
    email  = google_service_account.worker_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    startup-script = <<-EOF
                     #!/bin/bash
                     echo "export VAULT_AUTH_TYPE=gcp" >> /etc/profile.d/vault.sh
                     echo "export VAULT_AUTH_PRINCIPAL=gce-worker-role" >> /etc/profile.d/vault.sh
                     EOF
  }
}

# The GCP Auth Strategy will automatically query the local metadata server 
# to fetch the signed JWT required for Vault authentication.
```

### 2. Internal Vault Configuration (YAML Payload)
**Example Payload (`example_vault/admin/_auth_methods.yaml`)**:
```yaml
api_paths:
- api_path: v1/auth/gcp/role/gce-worker-role
  api_action: post
  api_payload:
    type: "gce"
    project_id: "my-project"
    bound_service_accounts: "vault-automation-sa@my-project.iam.gserviceaccount.com"
    policies: "automation-policy"
```
