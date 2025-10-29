# SoundHash Terraform Infrastructure

This directory contains Terraform configurations for provisioning AWS infrastructure for SoundHash.

## Quick Start

1. **Install Prerequisites**
   - [Terraform](https://www.terraform.io/downloads.html) >= 1.5
   - [AWS CLI](https://aws.amazon.com/cli/)
   - Configure AWS credentials: `aws configure`

2. **Set Variables**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Initialize Terraform**
   ```bash
   terraform init
   ```

4. **Review Plan**
   ```bash
   terraform plan
   ```

5. **Apply Configuration**
   ```bash
   terraform apply
   ```

## What Gets Created

- **Networking**: VPC with public, private, and database subnets across 3 AZs
- **Compute**: EKS cluster with on-demand and spot node groups
- **Database**: RDS PostgreSQL with Multi-AZ, encryption, and backups
- **Cache**: ElastiCache Redis cluster
- **Storage**: S3 bucket with encryption and lifecycle policies
- **Shared Storage**: EFS file system for Kubernetes persistent volumes
- **Security**: Security groups, IAM roles, KMS keys

## Estimated Costs

**Production Configuration** (approximate monthly costs):
- EKS Cluster: $73
- EC2 Nodes (3x t3.xlarge): $450
- RDS (db.r6g.xlarge Multi-AZ): $730
- ElastiCache (cache.r6g.large): $340
- EFS: $30 (varies with usage)
- Data Transfer: $50-100
- **Total**: ~$1,673-1,723/month

**Development Configuration** (with smaller instances):
- EKS Cluster: $73
- EC2 Nodes (1x t3.large): $75
- RDS (db.t4g.medium): $60
- ElastiCache (cache.t4g.micro): $12
- **Total**: ~$220/month

## Files

- `main.tf` - Provider and backend configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `vpc.tf` - VPC and networking resources
- `eks.tf` - EKS cluster and node groups
- `rds.tf` - PostgreSQL database
- `elasticache.tf` - Redis cache
- `s3.tf` - Object storage
- `terraform.tfvars` - Variable values (not in git)

## Important Notes

- **Never commit** `terraform.tfvars` or `*.tfstate` files
- Use remote state (S3 + DynamoDB) for team collaboration
- Enable deletion protection on RDS in production
- Review security groups before applying
- Set up cost alerts in AWS
- Regular backups are configured but verify them

## Documentation

See [docs/deployment/terraform.md](../docs/deployment/terraform.md) for detailed documentation.

## Support

For issues or questions, please open an issue in the repository.
