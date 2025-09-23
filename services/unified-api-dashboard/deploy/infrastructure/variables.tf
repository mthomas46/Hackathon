# Variables for Unified API Dashboard Infrastructure

variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "api-dashboard"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production"
  }
}

variable "owner" {
  description = "Owner of the infrastructure"
  type        = string
  default     = "platform-team"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "api-dashboard.local"
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"

  validation {
    condition = can(regex("^db\\.", var.db_instance_class))
    error_message = "Database instance class must start with 'db.'"
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 65536
    error_message = "Database allocated storage must be between 20 and 65536 GB"
  }
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "api_dashboard"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "dashboard"
}

# Redis Configuration
variable "redis_node_type" {
  description = "Redis node instance type"
  type        = string
  default     = "cache.t3.micro"

  validation {
    condition = can(regex("^cache\\.", var.redis_node_type))
    error_message = "Redis node type must start with 'cache.'"
  }
}

variable "redis_num_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1

  validation {
    condition     = var.redis_num_nodes >= 1 && var.redis_num_nodes <= 6
    error_message = "Redis number of nodes must be between 1 and 6"
  }
}

# Kubernetes Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.27"

  validation {
    condition = can(regex("^1\\.(2[4-9]|3[0-9])$", var.kubernetes_version))
    error_message = "Kubernetes version must be 1.24 or higher"
  }
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS nodes"
  type        = list(string)
  default     = ["t3.medium", "t3.large"]
}

variable "node_min_size" {
  description = "Minimum number of nodes in the node group"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of nodes in the node group"
  type        = number
  default     = 10
}

variable "node_desired_size" {
  description = "Desired number of nodes in the node group"
  type        = number
  default     = 3
}

variable "node_taints" {
  description = "Taints to apply to the node group"
  type = list(object({
    key    = string
    value  = optional(string)
    effect = string
  }))
  default = []
}

# Networking Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition = can(cidrnetmask(var.vpc_cidr))
    error_message = "VPC CIDR must be a valid CIDR block"
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = []
}

variable "public_subnets" {
  description = "List of public subnet CIDRs"
  type        = list(string)
  default     = [
    "10.0.1.0/24",
    "10.0.2.0/24",
    "10.0.3.0/24"
  ]
}

variable "private_subnets" {
  description = "List of private subnet CIDRs"
  type        = list(string)
  default     = [
    "10.0.101.0/24",
    "10.0.102.0/24",
    "10.0.103.0/24"
  ]
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable monitoring stack (Prometheus, Grafana)"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 30

  validation {
    condition     = var.log_retention_days >= 1 && var.log_retention_days <= 3653
    error_message = "Log retention days must be between 1 and 3653"
  }
}

variable "enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 3653
    error_message = "Backup retention days must be between 1 and 3653"
  }
}

# Security Configuration
variable "enable_waf" {
  description = "Enable Web Application Firewall"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Enable encryption at rest"
  type        = bool
  default     = true
}

variable "ssl_policy" {
  description = "SSL policy for load balancer"
  type        = string
  default     = "ELBSecurityPolicy-2016-08"

  validation {
    condition = contains([
      "ELBSecurityPolicy-2016-08",
      "ELBSecurityPolicy-TLS-1-2-2017-01",
      "ELBSecurityPolicy-TLS-1-2-Ext-2018-06",
      "ELBSecurityPolicy-FS-1-2-2019-08",
      "ELBSecurityPolicy-FS-1-2-Res-2019-08"
    ], var.ssl_policy)
    error_message = "SSL policy must be a valid AWS SSL policy"
  }
}

# High Availability Configuration
variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = true
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = true
}

# Cost Optimization
variable "enable_spot_instances" {
  description = "Use spot instances for cost optimization (not recommended for production)"
  type        = bool
  default     = false
}

variable "instance_warmup_period" {
  description = "Instance warmup period in seconds"
  type        = number
  default     = 300
}

# Tags
variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

# CloudWatch Configuration
variable "cloudwatch_alarm_cpu_threshold" {
  description = "CPU utilization threshold for CloudWatch alarms"
  type        = number
  default     = 80

  validation {
    condition     = var.cloudwatch_alarm_cpu_threshold >= 1 && var.cloudwatch_alarm_cpu_threshold <= 100
    error_message = "CPU threshold must be between 1 and 100"
  }
}

variable "cloudwatch_alarm_memory_threshold" {
  description = "Memory utilization threshold for CloudWatch alarms"
  type        = number
  default     = 80

  validation {
    condition     = var.cloudwatch_alarm_memory_threshold >= 1 && var.cloudwatch_alarm_memory_threshold <= 100
    error_message = "Memory threshold must be between 1 and 100"
  }
}

# EBS Configuration
variable "ebs_encrypted" {
  description = "Enable EBS encryption"
  type        = bool
  default     = true
}

variable "ebs_kms_key_rotation" {
  description = "Enable KMS key rotation"
  type        = bool
  default     = true
}

# Route 53 Configuration
variable "create_route53_record" {
  description = "Create Route 53 record for the load balancer"
  type        = bool
  default     = false
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID"
  type        = string
  default     = ""
}

# Budget Configuration
variable "enable_budget_alerts" {
  description = "Enable AWS Budget alerts"
  type        = bool
  default     = true
}

variable "monthly_budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 1000

  validation {
    condition     = var.monthly_budget_limit > 0
    error_message = "Monthly budget limit must be greater than 0"
  }
}

variable "budget_alert_thresholds" {
  description = "Budget alert thresholds (percentage)"
  type        = list(number)
  default     = [50, 75, 90, 100]

  validation {
    condition = alltrue([
      for threshold in var.budget_alert_thresholds : threshold >= 0 && threshold <= 100
    ])
    error_message = "Budget alert thresholds must be between 0 and 100"
  }
}
