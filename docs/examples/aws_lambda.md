# AWS Lambda Vault Integration

This example demonstrates how to inject the unified `VAULT_AUTH_*` variables into an AWS Lambda function via Terraform, and how to configure the corresponding auth method *inside* Vault using the provided YAML structures.

The `AWSAuthStrategy` uses `boto3` under the hood to generate a signed IAM request, which Vault verifies.

## 1. External Infrastructure (Terraform)

```hcl
resource "aws_lambda_function" "vault_worker" {
  filename      = "lambda_function_payload.zip"
  function_name = "vault_automation_worker"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "index.test"

  source_code_hash = filebase64sha256("lambda_function_payload.zip")

  runtime     = "python3.10"
  kms_key_arn = aws_kms_key.lambda_env_key.arn

  vpc_config {
    subnet_ids         = [aws_subnet.private_app.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  environment {
    variables = {
      # Unified Vault Auth Configuration
      VAULT_AUTH_TYPE      = "aws"
      # The principal is the name of the IAM Role that Vault is configured to trust
      VAULT_AUTH_PRINCIPAL = aws_iam_role.iam_for_lambda.name
      # VAULT_AUTH_SECRET is not needed for AWS IAM authentication as boto3 handles the signing
      
      # Optional: Target cluster config
      VAULT_CLUSTER        = "prod"
    }
  }
}
```

## 2. Internal Vault Configuration (YAML Payload)

To allow the Lambda function to authenticate, you must configure the `aws` auth method inside Vault. 
This is achieved by applying a YAML payload using the `bin/cluster_secret_data.py` tool.

**Example Payload (`example_vault/admin/_auth_methods.yaml`)**:
```yaml
api_paths:
- api_path: v1/auth/aws/role/vault_automation_worker
  api_action: post
  api_payload:
    auth_type: iam
    bound_iam_principal_arn: "arn:aws:iam::123456789012:role/iam_for_lambda"
    policies: "my-policy"
    max_ttl: "1h"
```

You apply this configuration by running:
```bash
python3 bin/cluster_secret_data.py --name example_vault --path ./config/example_vault/admin/_auth_methods.yaml
```
