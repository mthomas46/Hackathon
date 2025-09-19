"""Project Templates.

This module defines predefined project templates for different types of software projects,
providing quick-start configurations for common scenarios.
"""

from typing import Dict, Any
from datetime import datetime


# Built-in project templates
BUILT_IN_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "ecommerce_platform": {
        "id": "ecommerce_platform",
        "name": "AI-Powered E-commerce Platform",
        "description": "Complete e-commerce platform with AI recommendations, microservices architecture, and advanced analytics",
        "category": "Web Applications",
        "version": "2.0",
        "built_in": True,
        "tags": ["ecommerce", "ai", "microservices", "analytics", "recommendations"],
        "created_at": "2024-01-15T10:00:00Z",
        "estimated_duration_weeks": 16,
        "estimated_budget": 350000,
        "complexity": "complex",
        "configuration": {
            "project_name": "AI-Powered E-commerce Platform",
            "project_description": "A modern e-commerce platform with AI-driven recommendations, microservices architecture, and advanced analytics",
            "project_type": "web_application",
            "complexity_level": "complex",
            "simulation_type": "full_project",
            "duration_weeks": 16,
            "budget": 350000.0,
            "team_members": [
                {
                    "name": "Sarah Chen",
                    "role": "product_manager",
                    "expertise_level": "expert",
                    "productivity_multiplier": 0.95,
                    "skills": ["Product Strategy", "Agile Methodologies", "Stakeholder Management"],
                    "cost_per_hour": 75.0
                },
                {
                    "name": "Marcus Rodriguez",
                    "role": "technical_lead",
                    "expertise_level": "expert",
                    "productivity_multiplier": 1.2,
                    "skills": ["System Architecture", "Python", "Microservices", "AWS", "Kubernetes"],
                    "cost_per_hour": 85.0
                },
                {
                    "name": "Emily Johnson",
                    "role": "senior_developer",
                    "expertise_level": "senior",
                    "productivity_multiplier": 1.1,
                    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "React"],
                    "cost_per_hour": 65.0
                },
                {
                    "name": "David Kim",
                    "role": "senior_developer",
                    "expertise_level": "senior",
                    "productivity_multiplier": 1.1,
                    "skills": ["JavaScript", "React", "TypeScript", "GraphQL", "Node.js"],
                    "cost_per_hour": 65.0
                },
                {
                    "name": "Lisa Wong",
                    "role": "senior_developer",
                    "expertise_level": "senior",
                    "productivity_multiplier": 1.05,
                    "skills": ["Python", "Machine Learning", "TensorFlow", "Data Analysis", "AI Integration"],
                    "cost_per_hour": 70.0
                },
                {
                    "name": "James Park",
                    "role": "qa_engineer",
                    "expertise_level": "senior",
                    "productivity_multiplier": 1.0,
                    "skills": ["Test Automation", "Selenium", "pytest", "Performance Testing", "CI/CD"],
                    "cost_per_hour": 55.0
                },
                {
                    "name": "Anna Schmidt",
                    "role": "devops_engineer",
                    "expertise_level": "senior",
                    "productivity_multiplier": 1.0,
                    "skills": ["Docker", "Kubernetes", "AWS", "Terraform", "Monitoring"],
                    "cost_per_hour": 70.0
                }
            ],
            "timeline_phases": [
                {
                    "name": "Discovery & Planning",
                    "description": "Requirements gathering, stakeholder interviews, and project planning",
                    "duration_days": 20,
                    "deliverables": ["Business Requirements Document", "Technical Specifications", "Project Roadmap"],
                    "dependencies": []
                },
                {
                    "name": "System Architecture Design",
                    "description": "High-level and detailed system architecture design",
                    "duration_days": 25,
                    "deliverables": ["System Architecture Diagram", "API Specifications", "Database Design"],
                    "dependencies": ["Discovery & Planning"]
                },
                {
                    "name": "Core Development",
                    "description": "Implementation of core business logic and services",
                    "duration_days": 50,
                    "deliverables": ["User Management Service", "Product Catalog Service", "Order Processing Service"],
                    "dependencies": ["System Architecture Design"]
                },
                {
                    "name": "AI Integration",
                    "description": "Integration of AI/ML services for recommendations and analytics",
                    "duration_days": 30,
                    "deliverables": ["Recommendation Engine", "Personalization Service", "Analytics Dashboard"],
                    "dependencies": ["Core Development"]
                },
                {
                    "name": "Testing & QA",
                    "description": "Comprehensive testing, quality assurance, and performance optimization",
                    "duration_days": 25,
                    "deliverables": ["Unit Test Suite", "Integration Tests", "Performance Test Results"],
                    "dependencies": ["Core Development", "AI Integration"]
                },
                {
                    "name": "Deployment & Launch",
                    "description": "Production deployment, monitoring setup, and go-live activities",
                    "duration_days": 15,
                    "deliverables": ["Production Deployment", "Monitoring & Alerting Setup", "Documentation"],
                    "dependencies": ["Testing & QA"]
                }
            ],
            "include_document_generation": True,
            "include_workflow_execution": True,
            "include_team_dynamics": True,
            "real_time_progress": True,
            "max_execution_time_minutes": 180,
            "enable_ecosystem_integration": True
        }
    },

    "mobile_application": {
        "id": "mobile_application",
        "name": "Cross-Platform Mobile Application",
        "description": "Modern mobile app with native performance, offline capabilities, and seamless user experience",
        "category": "Mobile Applications",
        "version": "1.5",
        "built_in": True,
        "tags": ["mobile", "cross-platform", "react-native", "offline", "ux"],
        "created_at": "2024-01-20T14:30:00Z",
        "estimated_duration_weeks": 12,
        "estimated_budget": 180000,
        "complexity": "medium",
        "configuration": {
            "project_name": "Cross-Platform Mobile Application",
            "project_description": "Modern mobile application with native performance, offline capabilities, and seamless user experience",
            "project_type": "mobile_application",
            "complexity_level": "medium",
            "simulation_type": "full_project",
            "duration_weeks": 12,
            "budget": 180000.0,
            "team_members": [
                {
                    "name": "Alex Rivera",
                    "role": "product_manager",
                    "expertise_level": "senior",
                    "skills": ["Mobile UX", "Agile", "User Research"],
                    "cost_per_hour": 65.0
                },
                {
                    "name": "Jordan Lee",
                    "role": "mobile_developer",
                    "expertise_level": "senior",
                    "skills": ["React Native", "iOS", "Android", "JavaScript", "TypeScript"],
                    "cost_per_hour": 70.0
                },
                {
                    "name": "Taylor Swift",
                    "role": "mobile_developer",
                    "expertise_level": "senior",
                    "skills": ["Flutter", "Dart", "Mobile UI", "State Management"],
                    "cost_per_hour": 70.0
                },
                {
                    "name": "Morgan Chen",
                    "role": "ui_ux_designer",
                    "expertise_level": "senior",
                    "skills": ["Mobile Design", "Prototyping", "User Testing", "Figma"],
                    "cost_per_hour": 60.0
                },
                {
                    "name": "Casey Brown",
                    "role": "qa_engineer",
                    "expertise_level": "intermediate",
                    "skills": ["Mobile Testing", "Appium", "Device Testing", "Performance Testing"],
                    "cost_per_hour": 50.0
                }
            ],
            "timeline_phases": [
                {
                    "name": "Mobile Strategy & Research",
                    "description": "Market research, user interviews, and mobile strategy development",
                    "duration_days": 15,
                    "deliverables": ["Mobile Strategy Document", "User Personas", "Competitive Analysis"],
                    "dependencies": []
                },
                {
                    "name": "UI/UX Design",
                    "description": "Mobile-first design, wireframes, and interactive prototypes",
                    "duration_days": 20,
                    "deliverables": ["Mobile UI Kit", "User Flow Diagrams", "Interactive Prototype"],
                    "dependencies": ["Mobile Strategy & Research"]
                },
                {
                    "name": "Core Development",
                    "description": "Implementation of core mobile functionality and features",
                    "duration_days": 35,
                    "deliverables": ["Core App Architecture", "Authentication System", "Main Features"],
                    "dependencies": ["UI/UX Design"]
                },
                {
                    "name": "Advanced Features",
                    "description": "Offline support, push notifications, and advanced functionality",
                    "duration_days": 25,
                    "deliverables": ["Offline Mode", "Push Notifications", "Advanced Features"],
                    "dependencies": ["Core Development"]
                },
                {
                    "name": "Testing & Optimization",
                    "description": "Comprehensive testing, performance optimization, and device compatibility",
                    "duration_days": 15,
                    "deliverables": ["Test Reports", "Performance Benchmarks", "App Store Preparation"],
                    "dependencies": ["Advanced Features"]
                }
            ],
            "include_document_generation": True,
            "include_workflow_execution": True,
            "include_team_dynamics": True,
            "real_time_progress": True,
            "max_execution_time_minutes": 120,
            "enable_ecosystem_integration": False
        }
    },

    "api_service": {
        "id": "api_service",
        "name": "RESTful API Service",
        "description": "High-performance REST API with comprehensive documentation, authentication, and monitoring",
        "category": "API Services",
        "version": "1.8",
        "built_in": True,
        "tags": ["api", "rest", "microservice", "documentation", "authentication"],
        "created_at": "2024-01-25T09:15:00Z",
        "estimated_duration_weeks": 8,
        "estimated_budget": 95000,
        "complexity": "medium",
        "configuration": {
            "project_name": "RESTful API Service",
            "project_description": "High-performance REST API with comprehensive documentation, authentication, and monitoring",
            "project_type": "api_service",
            "complexity_level": "medium",
            "simulation_type": "full_project",
            "duration_weeks": 8,
            "budget": 95000.0,
            "team_members": [
                {
                    "name": "Dr. API Smith",
                    "role": "technical_lead",
                    "expertise_level": "expert",
                    "skills": ["API Design", "Python", "FastAPI", "PostgreSQL", "Redis"],
                    "cost_per_hour": 80.0
                },
                {
                    "name": "Backend Dev",
                    "role": "senior_developer",
                    "expertise_level": "senior",
                    "skills": ["Python", "FastAPI", "SQLAlchemy", "Docker", "Testing"],
                    "cost_per_hour": 65.0
                },
                {
                    "name": "DevOps Engineer",
                    "role": "devops_engineer",
                    "expertise_level": "senior",
                    "skills": ["Docker", "Kubernetes", "CI/CD", "Monitoring", "AWS"],
                    "cost_per_hour": 70.0
                },
                {
                    "name": "QA Specialist",
                    "role": "qa_engineer",
                    "expertise_level": "intermediate",
                    "skills": ["API Testing", "Postman", "Load Testing", "Security Testing"],
                    "cost_per_hour": 50.0
                }
            ],
            "timeline_phases": [
                {
                    "name": "API Design & Planning",
                    "description": "API specification, resource modeling, and technical planning",
                    "duration_days": 10,
                    "deliverables": ["OpenAPI Specification", "Database Schema", "Architecture Diagram"],
                    "dependencies": []
                },
                {
                    "name": "Core API Development",
                    "description": "Implementation of core API endpoints and business logic",
                    "duration_days": 20,
                    "deliverables": ["Core Endpoints", "Data Models", "Authentication System"],
                    "dependencies": ["API Design & Planning"]
                },
                {
                    "name": "API Enhancement",
                    "description": "Caching, rate limiting, documentation, and advanced features",
                    "duration_days": 15,
                    "deliverables": ["API Documentation", "Caching Layer", "Monitoring Setup"],
                    "dependencies": ["Core API Development"]
                },
                {
                    "name": "Testing & Deployment",
                    "description": "Comprehensive testing, performance optimization, and deployment",
                    "duration_days": 10,
                    "deliverables": ["Test Suite", "Performance Report", "Production Deployment"],
                    "dependencies": ["API Enhancement"]
                }
            ],
            "include_document_generation": True,
            "include_workflow_execution": True,
            "include_team_dynamics": True,
            "real_time_progress": True,
            "max_execution_time_minutes": 90,
            "enable_ecosystem_integration": False
        }
    },

    "microservices_architecture": {
        "id": "microservices_architecture",
        "name": "Microservices Architecture",
        "description": "Distributed system with multiple independent services, service mesh, and advanced orchestration",
        "category": "Microservices",
        "version": "2.2",
        "built_in": True,
        "tags": ["microservices", "kubernetes", "docker", "service-mesh", "distributed"],
        "created_at": "2024-02-01T11:45:00Z",
        "estimated_duration_weeks": 20,
        "estimated_budget": 425000,
        "complexity": "complex",
        "configuration": {
            "project_name": "Microservices Architecture",
            "project_description": "Distributed system with multiple independent services, service mesh, and advanced orchestration",
            "project_type": "microservices",
            "complexity_level": "complex",
            "simulation_type": "full_project",
            "duration_weeks": 20,
            "budget": 425000.0,
            "team_members": [
                {
                    "name": "Microservice Architect",
                    "role": "architect",
                    "expertise_level": "expert",
                    "skills": ["Microservices", "Domain-Driven Design", "Event Sourcing", "CQRS"],
                    "cost_per_hour": 90.0
                },
                {
                    "name": "Platform Engineer",
                    "role": "devops_engineer",
                    "expertise_level": "expert",
                    "skills": ["Kubernetes", "Istio", "Helm", "Terraform", "AWS"],
                    "cost_per_hour": 85.0
                },
                {
                    "name": "Service Developer 1",
                    "role": "senior_developer",
                    "expertise_level": "senior",
                    "skills": ["Go", "Python", "gRPC", "Docker", "Kubernetes"],
                    "cost_per_hour": 75.0
                },
                {
                    "name": "Service Developer 2",
                    "role": "senior_developer",
                    "expertise_level": "senior",
                    "skills": ["Java", "Spring Boot", "PostgreSQL", "Redis", "Kafka"],
                    "cost_per_hour": 75.0
                },
                {
                    "name": "Service Developer 3",
                    "role": "senior_developer",
                    "expertise_level": "senior",
                    "skills": ["Node.js", "TypeScript", "MongoDB", "RabbitMQ", "Docker"],
                    "cost_per_hour": 75.0
                },
                {
                    "name": "SRE Engineer",
                    "role": "devops_engineer",
                    "expertise_level": "senior",
                    "skills": ["Monitoring", "Alerting", "SLO/SLI", "Prometheus", "Grafana"],
                    "cost_per_hour": 80.0
                },
                {
                    "name": "Security Engineer",
                    "role": "security_engineer",
                    "expertise_level": "senior",
                    "skills": ["Security", "OAuth", "JWT", "Encryption", "Compliance"],
                    "cost_per_hour": 85.0
                },
                {
                    "name": "QA Lead",
                    "role": "qa_engineer",
                    "expertise_level": "senior",
                    "skills": ["Integration Testing", "Contract Testing", "Chaos Engineering", "Performance Testing"],
                    "cost_per_hour": 65.0
                }
            ],
            "timeline_phases": [
                {
                    "name": "Domain Analysis & Design",
                    "description": "Domain modeling, bounded contexts, and microservice boundaries",
                    "duration_days": 25,
                    "deliverables": ["Domain Model", "Bounded Contexts", "Service Contracts"],
                    "dependencies": []
                },
                {
                    "name": "Platform Setup",
                    "description": "Kubernetes cluster, service mesh, and CI/CD pipelines",
                    "duration_days": 20,
                    "deliverables": ["K8s Cluster", "Istio Mesh", "CI/CD Pipelines"],
                    "dependencies": ["Domain Analysis & Design"]
                },
                {
                    "name": "Core Services Development",
                    "description": "Implementation of core business microservices",
                    "duration_days": 45,
                    "deliverables": ["User Service", "Product Service", "Order Service", "Payment Service"],
                    "dependencies": ["Platform Setup"]
                },
                {
                    "name": "Supporting Services",
                    "description": "API gateway, service discovery, and cross-cutting concerns",
                    "duration_days": 30,
                    "deliverables": ["API Gateway", "Service Discovery", "Authentication Service"],
                    "dependencies": ["Core Services Development"]
                },
                {
                    "name": "Integration & Testing",
                    "description": "Service integration testing, contract testing, and end-to-end testing",
                    "duration_days": 25,
                    "deliverables": ["Integration Tests", "Contract Tests", "E2E Test Suite"],
                    "dependencies": ["Supporting Services"]
                },
                {
                    "name": "Deployment & Operations",
                    "description": "Production deployment, monitoring, and operational procedures",
                    "duration_days": 20,
                    "deliverables": ["Production Deployment", "Monitoring Stack", "Operational Runbooks"],
                    "dependencies": ["Integration & Testing"]
                }
            ],
            "include_document_generation": True,
            "include_workflow_execution": True,
            "include_team_dynamics": True,
            "real_time_progress": True,
            "max_execution_time_minutes": 240,
            "enable_ecosystem_integration": True
        }
    },

    "data_pipeline": {
        "id": "data_pipeline",
        "name": "Advanced Data Pipeline",
        "description": "ETL/ELT pipeline for data processing, analytics, and machine learning workflows",
        "category": "Data Engineering",
        "version": "1.9",
        "built_in": True,
        "tags": ["data", "pipeline", "etl", "analytics", "airflow", "spark"],
        "created_at": "2024-02-05T13:20:00Z",
        "estimated_duration_weeks": 14,
        "estimated_budget": 245000,
        "complexity": "complex",
        "configuration": {
            "project_name": "Advanced Data Pipeline",
            "project_description": "ETL/ELT pipeline for data processing, analytics, and machine learning workflows",
            "project_type": "data_pipeline",
            "complexity_level": "complex",
            "simulation_type": "full_project",
            "duration_weeks": 14,
            "budget": 245000.0,
            "team_members": [
                {
                    "name": "Data Architect",
                    "role": "architect",
                    "expertise_level": "expert",
                    "skills": ["Data Architecture", "Data Modeling", "ETL Design", "Data Warehousing"],
                    "cost_per_hour": 85.0
                },
                {
                    "name": "Data Engineer 1",
                    "role": "data_engineer",
                    "expertise_level": "senior",
                    "skills": ["Python", "Apache Airflow", "SQL", "PostgreSQL", "Docker"],
                    "cost_per_hour": 70.0
                },
                {
                    "name": "Data Engineer 2",
                    "role": "data_engineer",
                    "expertise_level": "senior",
                    "skills": ["PySpark", "Hadoop", "Kafka", "AWS EMR", "Terraform"],
                    "cost_per_hour": 70.0
                },
                {
                    "name": "Data Analyst",
                    "role": "data_analyst",
                    "expertise_level": "senior",
                    "skills": ["SQL", "Python", "Tableau", "Data Visualization", "Statistics"],
                    "cost_per_hour": 65.0
                },
                {
                    "name": "ML Engineer",
                    "role": "ml_engineer",
                    "expertise_level": "senior",
                    "skills": ["Python", "scikit-learn", "TensorFlow", "MLflow", "Feature Engineering"],
                    "cost_per_hour": 75.0
                },
                {
                    "name": "DevOps Engineer",
                    "role": "devops_engineer",
                    "expertise_level": "intermediate",
                    "skills": ["Docker", "Kubernetes", "CI/CD", "AWS", "Monitoring"],
                    "cost_per_hour": 60.0
                }
            ],
            "timeline_phases": [
                {
                    "name": "Data Architecture Design",
                    "description": "Data modeling, pipeline architecture, and technology selection",
                    "duration_days": 18,
                    "deliverables": ["Data Architecture Diagram", "Pipeline Design", "Technology Stack"],
                    "dependencies": []
                },
                {
                    "name": "Data Ingestion Setup",
                    "description": "Data source connections, ingestion pipelines, and data quality checks",
                    "duration_days": 20,
                    "deliverables": ["Ingestion Pipelines", "Data Quality Framework", "Source Connectors"],
                    "dependencies": ["Data Architecture Design"]
                },
                {
                    "name": "Data Processing Pipeline",
                    "description": "ETL/ELT transformations, data cleansing, and processing workflows",
                    "duration_days": 25,
                    "deliverables": ["Transformation Logic", "Data Processing Jobs", "Workflow Orchestration"],
                    "dependencies": ["Data Ingestion Setup"]
                },
                {
                    "name": "Data Storage & Analytics",
                    "description": "Data warehouse setup, analytics queries, and reporting dashboards",
                    "duration_days": 20,
                    "deliverables": ["Data Warehouse", "Analytics Queries", "Reporting Dashboards"],
                    "dependencies": ["Data Processing Pipeline"]
                },
                {
                    "name": "ML Integration",
                    "description": "Machine learning model training and deployment pipelines",
                    "duration_days": 15,
                    "deliverables": ["ML Training Pipeline", "Model Deployment", "Prediction Service"],
                    "dependencies": ["Data Storage & Analytics"]
                },
                {
                    "name": "Monitoring & Optimization",
                    "description": "Pipeline monitoring, performance optimization, and operational procedures",
                    "duration_days": 12,
                    "deliverables": ["Monitoring Dashboard", "Performance Reports", "Operational Runbooks"],
                    "dependencies": ["ML Integration"]
                }
            ],
            "include_document_generation": True,
            "include_workflow_execution": True,
            "include_team_dynamics": True,
            "real_time_progress": True,
            "max_execution_time_minutes": 150,
            "enable_ecosystem_integration": True
        }
    },

    "machine_learning_project": {
        "id": "machine_learning_project",
        "name": "Machine Learning Solution",
        "description": "End-to-end ML solution with model training, deployment, monitoring, and MLOps practices",
        "category": "Machine Learning",
        "version": "2.1",
        "built_in": True,
        "tags": ["ml", "ai", "mops", "model-training", "deployment", "monitoring"],
        "created_at": "2024-02-10T16:00:00Z",
        "estimated_duration_weeks": 18,
        "estimated_budget": 320000,
        "complexity": "complex",
        "configuration": {
            "project_name": "Machine Learning Solution",
            "project_description": "End-to-end ML solution with model training, deployment, monitoring, and MLOps practices",
            "project_type": "machine_learning",
            "complexity_level": "complex",
            "simulation_type": "full_project",
            "duration_weeks": 18,
            "budget": 320000.0,
            "team_members": [
                {
                    "name": "ML Architect",
                    "role": "architect",
                    "expertise_level": "expert",
                    "skills": ["ML Architecture", "Model Design", "Scalability", "MLOps"],
                    "cost_per_hour": 95.0
                },
                {
                    "name": "Data Scientist 1",
                    "role": "data_scientist",
                    "expertise_level": "expert",
                    "skills": ["Python", "scikit-learn", "TensorFlow", "Feature Engineering", "Model Selection"],
                    "cost_per_hour": 80.0
                },
                {
                    "name": "Data Scientist 2",
                    "role": "data_scientist",
                    "expertise_level": "senior",
                    "skills": ["Python", "PyTorch", "NLP", "Computer Vision", "Experiment Tracking"],
                    "cost_per_hour": 75.0
                },
                {
                    "name": "ML Engineer",
                    "role": "ml_engineer",
                    "expertise_level": "senior",
                    "skills": ["Python", "MLflow", "Kubeflow", "Model Deployment", "Kubernetes"],
                    "cost_per_hour": 75.0
                },
                {
                    "name": "Data Engineer",
                    "role": "data_engineer",
                    "expertise_level": "senior",
                    "skills": ["Python", "Apache Spark", "Data Processing", "Feature Stores", "SQL"],
                    "cost_per_hour": 70.0
                },
                {
                    "name": "MLOps Engineer",
                    "role": "devops_engineer",
                    "expertise_level": "senior",
                    "skills": ["Docker", "Kubernetes", "CI/CD", "Monitoring", "Terraform"],
                    "cost_per_hour": 75.0
                },
                {
                    "name": "Research Scientist",
                    "role": "research_scientist",
                    "expertise_level": "expert",
                    "skills": ["Advanced ML", "Research", "Paper Implementation", "Innovation"],
                    "cost_per_hour": 100.0
                }
            ],
            "timeline_phases": [
                {
                    "name": "Problem Definition & Data Strategy",
                    "description": "Business problem definition, success metrics, and data strategy development",
                    "duration_days": 20,
                    "deliverables": ["Problem Statement", "Success Metrics", "Data Strategy", "Initial Dataset"],
                    "dependencies": []
                },
                {
                    "name": "Data Engineering & Preparation",
                    "description": "Data collection, preprocessing, feature engineering, and data pipeline setup",
                    "duration_days": 25,
                    "deliverables": ["Data Pipeline", "Feature Store", "Data Quality Framework", "Training Dataset"],
                    "dependencies": ["Problem Definition & Data Strategy"]
                },
                {
                    "name": "Model Development & Training",
                    "description": "Model selection, training, hyperparameter tuning, and experiment tracking",
                    "duration_days": 30,
                    "deliverables": ["Trained Models", "Model Registry", "Experiment Results", "Model Documentation"],
                    "dependencies": ["Data Engineering & Preparation"]
                },
                {
                    "name": "Model Evaluation & Validation",
                    "description": "Model evaluation, validation, bias testing, and performance benchmarking",
                    "duration_days": 20,
                    "deliverables": ["Model Evaluation Report", "Validation Results", "Bias Analysis", "Performance Benchmarks"],
                    "dependencies": ["Model Development & Training"]
                },
                {
                    "name": "MLOps & Deployment",
                    "description": "Model deployment, monitoring setup, and operational infrastructure",
                    "duration_days": 25,
                    "deliverables": ["Model Deployment", "Monitoring Stack", "Prediction Service", "Operational Procedures"],
                    "dependencies": ["Model Evaluation & Validation"]
                },
                {
                    "name": "Production Monitoring & Optimization",
                    "description": "Production monitoring, model retraining, and continuous optimization",
                    "duration_days": 18,
                    "deliverables": ["Monitoring Dashboard", "Retraining Pipeline", "Optimization Report", "Maintenance Procedures"],
                    "dependencies": ["MLOps & Deployment"]
                }
            ],
            "include_document_generation": True,
            "include_workflow_execution": True,
            "include_team_dynamics": True,
            "real_time_progress": True,
            "max_execution_time_minutes": 200,
            "enable_ecosystem_integration": True
        }
    }
}


def get_template_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """Get all templates for a specific category."""
    return {
        template_id: template
        for template_id, template in BUILT_IN_TEMPLATES.items()
        if template.get('category', '').lower() == category.lower()
    }


def get_template_by_complexity(complexity: str) -> Dict[str, Dict[str, Any]]:
    """Get all templates for a specific complexity level."""
    return {
        template_id: template
        for template_id, template in BUILT_IN_TEMPLATES.items()
        if template.get('complexity', '').lower() == complexity.lower()
    }


def get_popular_templates(limit: int = 5) -> List[Dict[str, Any]]:
    """Get most popular templates based on usage patterns."""
    # In a real implementation, this would be based on actual usage data
    # For now, return a curated selection
    popular_ids = ['ecommerce_platform', 'mobile_application', 'api_service', 'microservices_architecture']
    return [BUILT_IN_TEMPLATES[tid] for tid in popular_ids if tid in BUILT_IN_TEMPLATES][:limit]


def get_quick_start_templates() -> List[Dict[str, Any]]:
    """Get templates suitable for quick start scenarios."""
    quick_start_ids = ['api_service', 'mobile_application', 'ecommerce_platform']
    return [BUILT_IN_TEMPLATES[tid] for tid in quick_start_ids if tid in BUILT_IN_TEMPLATES]


def get_enterprise_templates() -> List[Dict[str, Any]]:
    """Get templates suitable for enterprise scenarios."""
    enterprise_ids = ['microservices_architecture', 'data_pipeline', 'machine_learning_project']
    return [BUILT_IN_TEMPLATES[tid] for tid in enterprise_ids if tid in BUILT_IN_TEMPLATES]


def get_template_recommendations(
    project_size: str = "medium",
    timeline: str = "standard",
    budget: str = "medium"
) -> List[Dict[str, Any]]:
    """Get template recommendations based on project parameters."""
    recommendations = []

    # Simple recommendation logic based on parameters
    if project_size == "small" and timeline == "quick":
        recommendations = [BUILT_IN_TEMPLATES.get('api_service')]
    elif project_size == "medium" and budget == "high":
        recommendations = [
            BUILT_IN_TEMPLATES.get('mobile_application'),
            BUILT_IN_TEMPLATES.get('ecommerce_platform')
        ]
    elif project_size == "large" or budget == "high":
        recommendations = [
            BUILT_IN_TEMPLATES.get('microservices_architecture'),
            BUILT_IN_TEMPLATES.get('data_pipeline'),
            BUILT_IN_TEMPLATES.get('machine_learning_project')
        ]
    else:
        recommendations = get_popular_templates(3)

    return [rec for rec in recommendations if rec is not None]
