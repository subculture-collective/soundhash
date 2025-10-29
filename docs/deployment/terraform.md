# Terraform Infrastructure Guide

This guide covers provisioning AWS infrastructure for SoundHash using Terraform.

## Prerequisites

- Terraform >= 1.5
- AWS CLI configured with appropriate credentials
- AWS account with necessary permissions

## Infrastructure Components

The Terraform configuration provisions:

- **VPC**: Multi-AZ VPC with public, private, and database subnets
- **EKS**: Managed Kubernetes cluster with node groups
- **RDS**: PostgreSQL database with Multi-AZ deployment
- **ElastiCache**: Redis cluster for caching
- **S3**: Object storage bucket
- **EFS**: Elastic File System for shared storage
- **Security Groups**: Properly configured network security
- **IAM Roles**: Service accounts and policies

## Directory Structure

```
terraform/
├── main.tf           # Main configuration and provider setup
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── vpc.tf           # VPC and networking
├── eks.tf           # EKS cluster configuration
├── rds.tf           # PostgreSQL RDS
├── elasticache.tf   # Redis ElastiCache
├── s3.tf            # S3 bucket
└── terraform.tfvars # Variable values (not in git)
```

## Getting Started

### 1. Configure Variables

Create a `terraform.tfvars` file:

```hcl
aws_region  = "us-east-1"
environment = "production"

# Database credentials (use AWS Secrets Manager in production)
db_username = "soundhash_admin"
db_password = "CHANGE_ME_SECURE_PASSWORD"

# Customize as needed
eks_cluster_version = "1.28"
db_instance_class   = "db.r6g.xlarge"
redis_node_type     = "cache.r6g.large"
```

**Important**: Never commit `terraform.tfvars` to version control. Add it to `.gitignore`.

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

This downloads required providers and modules.

### 3. Plan Infrastructure

```bash
terraform plan
```

Review the planned changes before applying.

### 4. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted to create the infrastructure.

This will take 15-20 minutes to provision all resources.

### 5. Configure kubectl

After EKS is created, configure kubectl:

```bash
aws eks update-kubeconfig --region us-east-1 --name soundhash-production
```

Or use the output command:

```bash
$(terraform output -raw configure_kubectl)
```

### 6. Verify Cluster

```bash
kubectl get nodes
kubectl get namespaces
```

## State Management

### Remote State (Recommended for Teams)

Configure S3 backend in `main.tf`:

```hcl
terraform {
  backend "s3" {
    bucket         = "soundhash-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

Create the S3 bucket and DynamoDB table first:

```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket soundhash-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket soundhash-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

Then initialize with the backend:

```bash
terraform init -migrate-state
```

## Outputs

After applying, Terraform provides important outputs:

```bash
# View all outputs
terraform output

# View specific output
terraform output rds_endpoint
terraform output eks_cluster_endpoint
```

### Key Outputs

- **vpc_id**: VPC identifier
- **eks_cluster_endpoint**: EKS API endpoint
- **rds_endpoint**: PostgreSQL connection endpoint
- **redis_endpoint**: Redis connection endpoint
- **s3_bucket_name**: Storage bucket name
- **efs_id**: EFS file system ID

## Customization

### Node Groups

Modify `variables.tf` to customize EKS node groups:

```hcl
variable "eks_node_groups" {
  default = {
    general = {
      desired_size   = 5
      min_size       = 3
      max_size       = 15
      instance_types = ["t3.2xlarge"]
      capacity_type  = "ON_DEMAND"
    }
  }
}
```

### Database Size

Adjust RDS configuration:

```hcl
variable "db_instance_class" {
  default = "db.r6g.2xlarge"
}

variable "db_allocated_storage" {
  default = 200
}
```

### Multiple Environments

Create separate workspaces:

```bash
# Create staging workspace
terraform workspace new staging

# Switch to production
terraform workspace select production

# List workspaces
terraform workspace list
```

Or use separate state files:

```bash
# Staging
terraform apply -var-file=staging.tfvars

# Production
terraform apply -var-file=production.tfvars
```

## Updating Infrastructure

### Apply Changes

```bash
terraform plan
terraform apply
```

### Target Specific Resources

```bash
terraform apply -target=module.eks
terraform apply -target=aws_db_instance.postgres
```

### Refresh State

```bash
terraform refresh
```

## Destroying Infrastructure

**Warning**: This will delete all resources and data!

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy infrastructure
terraform destroy
```

For production, consider:
1. Taking database snapshots first
2. Backing up S3 data
3. Exporting any important logs

## Cost Optimization

### Development Environment

```hcl
# Smaller instances
db_instance_class = "db.t4g.medium"
redis_node_type   = "cache.t4g.micro"

# Reduce node count
eks_node_groups = {
  general = {
    desired_size = 1
    min_size     = 1
    max_size     = 2
  }
}

# Disable Multi-AZ
# In rds.tf, set: multi_az = false
```

### Use Spot Instances

The configuration includes a spot node group by default:

```hcl
spot = {
  desired_size   = 2
  min_size       = 0
  max_size       = 8
  instance_types = ["t3.large", "t3.xlarge"]
  capacity_type  = "SPOT"
}
```

## Security Best Practices

1. **Secrets Management**
   - Use AWS Secrets Manager for sensitive data
   - Never commit credentials to version control
   - Rotate credentials regularly

2. **Network Security**
   - Private subnets for workloads
   - Security groups with minimal access
   - VPC Flow Logs enabled

3. **Encryption**
   - KMS encryption for RDS, EFS, S3
   - TLS for all network traffic
   - Encrypted EBS volumes

4. **Monitoring**
   - CloudWatch logs enabled
   - Performance Insights for RDS
   - VPC Flow Logs
   - Enhanced monitoring

5. **Backups**
   - 30-day retention for RDS
   - S3 versioning enabled
   - Automated snapshots

## Troubleshooting

### Module Download Issues

```bash
terraform init -upgrade
```

### State Lock Issues

```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

### Provider Version Conflicts

```bash
terraform init -upgrade
```

### Resource Already Exists

```bash
# Import existing resource
terraform import aws_s3_bucket.storage soundhash-storage-prod
```

## Advanced Topics

### Multi-Region Deployment

1. Create separate Terraform configurations per region
2. Use Route53 for global load balancing
3. Set up cross-region RDS read replicas
4. Configure S3 cross-region replication

### Disaster Recovery

1. Regular RDS snapshots
2. Cross-region backup replication
3. Infrastructure as Code (this Terraform config)
4. Documented recovery procedures

### Blue-Green Deployment

1. Create new EKS cluster
2. Deploy application to new cluster
3. Switch traffic at load balancer
4. Destroy old cluster

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Terraform Apply
  run: |
    cd terraform
    terraform init
    terraform apply -auto-approve
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

### GitLab CI Example

```yaml
terraform:
  image: hashicorp/terraform:latest
  script:
    - cd terraform
    - terraform init
    - terraform plan
    - terraform apply -auto-approve
```

## Module Documentation

- [AWS VPC Module](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws)
- [AWS EKS Module](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws)

## Next Steps

1. Set up AWS Systems Manager for parameter management
2. Configure AWS CloudWatch for monitoring
3. Set up AWS CloudTrail for audit logging
4. Implement AWS Config for compliance
5. Configure AWS Backup for automated backups
6. Set up Cost Explorer and billing alerts
