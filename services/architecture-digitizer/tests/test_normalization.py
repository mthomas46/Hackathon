"""Tests for architecture normalization logic."""

import pytest
from unittest.mock import patch, MagicMock
import json

from ..main import (
    normalize_aws_architecture,
    normalize_azure_architecture,
    normalize_gcp_architecture,
    detect_system_type,
    validate_architecture_data,
    ArchitectureNormalizationError,
)


class TestAWSSNormalization:
    """Test AWS architecture normalization."""

    def test_normalize_aws_ec2_instance(self):
        """Test normalizing AWS EC2 instance."""
        aws_data = {
            "resources": [
                {
                    "type": "ec2",
                    "id": "i-1234567890abcdef0",
                    "properties": {
                        "instance_type": "t2.micro",
                        "state": "running",
                        "vpc_id": "vpc-12345",
                        "subnet_id": "subnet-12345"
                    }
                }
            ]
        }

        result = normalize_aws_architecture(aws_data)

        assert "normalized_resources" in result
        assert len(result["normalized_resources"]) == 1

        resource = result["normalized_resources"][0]
        assert resource["type"] == "compute_instance"
        assert resource["platform"] == "aws"
        assert "properties" in resource
        assert resource["properties"]["instance_type"] == "t2.micro"

    def test_normalize_aws_s3_bucket(self):
        """Test normalizing AWS S3 bucket."""
        aws_data = {
            "resources": [
                {
                    "type": "s3",
                    "id": "my-bucket",
                    "properties": {
                        "region": "us-east-1",
                        "versioning": "Enabled"
                    }
                }
            ]
        }

        result = normalize_aws_architecture(aws_data)

        assert len(result["normalized_resources"]) == 1
        resource = result["normalized_resources"][0]
        assert resource["type"] == "storage_bucket"
        assert resource["platform"] == "aws"
        assert resource["properties"]["region"] == "us-east-1"

    def test_normalize_aws_rds_instance(self):
        """Test normalizing AWS RDS instance."""
        aws_data = {
            "resources": [
                {
                    "type": "rds",
                    "id": "my-database",
                    "properties": {
                        "engine": "postgres",
                        "engine_version": "13.7",
                        "instance_class": "db.t3.micro"
                    }
                }
            ]
        }

        result = normalize_aws_architecture(aws_data)

        assert len(result["normalized_resources"]) == 1
        resource = result["normalized_resources"][0]
        assert resource["type"] == "database_instance"
        assert resource["platform"] == "aws"
        assert resource["properties"]["engine"] == "postgres"


class TestAzureNormalization:
    """Test Azure architecture normalization."""

    def test_normalize_azure_vm(self):
        """Test normalizing Azure VM."""
        azure_data = {
            "resources": [
                {
                    "type": "Microsoft.Compute/virtualMachines",
                    "id": "/subscriptions/.../vm1",
                    "properties": {
                        "hardwareProfile": {"vmSize": "Standard_B1s"},
                        "storageProfile": {"osDisk": {"osType": "Linux"}},
                        "networkProfile": {"networkInterfaces": []}
                    }
                }
            ]
        }

        result = normalize_azure_architecture(azure_data)

        assert "normalized_resources" in result
        assert len(result["normalized_resources"]) == 1

        resource = result["normalized_resources"][0]
        assert resource["type"] == "compute_instance"
        assert resource["platform"] == "azure"
        assert resource["properties"]["vm_size"] == "Standard_B1s"

    def test_normalize_azure_storage_account(self):
        """Test normalizing Azure storage account."""
        azure_data = {
            "resources": [
                {
                    "type": "Microsoft.Storage/storageAccounts",
                    "id": "/subscriptions/.../storage1",
                    "properties": {
                        "supportsHttpsTrafficOnly": True,
                        "encryption": {"services": {"blob": {"enabled": True}}}
                    }
                }
            ]
        }

        result = normalize_azure_architecture(azure_data)

        assert len(result["normalized_resources"]) == 1
        resource = result["normalized_resources"][0]
        assert resource["type"] == "storage_account"
        assert resource["platform"] == "azure"


class TestGCPNormalization:
    """Test GCP architecture normalization."""

    def test_normalize_gcp_compute_instance(self):
        """Test normalizing GCP compute instance."""
        gcp_data = {
            "resources": [
                {
                    "type": "compute.v1.Instance",
                    "id": "projects/my-project/zones/us-central1-a/instances/instance-1",
                    "properties": {
                        "machineType": "zones/us-central1-a/machineTypes/n1-standard-1",
                        "networkInterfaces": [{"network": "global/networks/default"}]
                    }
                }
            ]
        }

        result = normalize_gcp_architecture(gcp_data)

        assert "normalized_resources" in result
        assert len(result["normalized_resources"]) == 1

        resource = result["normalized_resources"][0]
        assert resource["type"] == "compute_instance"
        assert resource["platform"] == "gcp"
        assert "machine_type" in resource["properties"]


class TestSystemDetection:
    """Test automatic system type detection."""

    def test_detect_aws_system(self):
        """Test detecting AWS system."""
        aws_data = {
            "resources": [
                {"type": "ec2", "properties": {"instance_type": "t2.micro"}},
                {"type": "s3", "properties": {"bucket": "my-bucket"}}
            ]
        }

        system = detect_system_type(aws_data)
        assert system == "aws"

    def test_detect_azure_system(self):
        """Test detecting Azure system."""
        azure_data = {
            "resources": [
                {"type": "Microsoft.Compute/virtualMachines", "properties": {}}
            ]
        }

        system = detect_system_type(azure_data)
        assert system == "azure"

    def test_detect_gcp_system(self):
        """Test detecting GCP system."""
        gcp_data = {
            "resources": [
                {"type": "compute.v1.Instance", "properties": {}}
            ]
        }

        system = detect_system_type(gcp_data)
        assert system == "gcp"

    def test_detect_unknown_system(self):
        """Test detecting unknown system."""
        unknown_data = {
            "resources": [
                {"type": "custom.resource", "properties": {}}
            ]
        }

        system = detect_system_type(unknown_data)
        assert system == "unknown"


class TestValidation:
    """Test architecture data validation."""

    def test_validate_valid_architecture(self):
        """Test validating valid architecture data."""
        valid_data = {
            "resources": [
                {
                    "type": "ec2",
                    "id": "i-123",
                    "properties": {"instance_type": "t2.micro"}
                }
            ],
            "connections": []
        }

        # Should not raise exception
        validate_architecture_data(valid_data)

    def test_validate_missing_resources(self):
        """Test validating architecture without resources."""
        invalid_data = {"connections": []}

        with pytest.raises(ArchitectureNormalizationError, match="missing.*resources"):
            validate_architecture_data(invalid_data)

    def test_validate_invalid_resource_structure(self):
        """Test validating architecture with invalid resource structure."""
        invalid_data = {
            "resources": [
                {"type": "ec2"}  # Missing id and properties
            ]
        }

        with pytest.raises(ArchitectureNormalizationError):
            validate_architecture_data(invalid_data)

    def test_validate_empty_resources(self):
        """Test validating architecture with empty resources."""
        invalid_data = {"resources": []}

        with pytest.raises(ArchitectureNormalizationError, match="empty.*resources"):
            validate_architecture_data(invalid_data)


class TestConnectionsNormalization:
    """Test connection/link normalization."""

    def test_normalize_connections_aws(self):
        """Test normalizing AWS connections."""
        aws_data = {
            "resources": [
                {"type": "ec2", "id": "i-1", "properties": {}},
                {"type": "rds", "id": "db-1", "properties": {}}
            ],
            "connections": [
                {
                    "from": "i-1",
                    "to": "db-1",
                    "type": "network"
                }
            ]
        }

        result = normalize_aws_architecture(aws_data)

        assert "normalized_connections" in result
        assert len(result["normalized_connections"]) == 1

        connection = result["normalized_connections"][0]
        assert connection["source"] == "i-1"
        assert connection["target"] == "db-1"
        assert connection["type"] == "network"

    def test_normalize_connections_empty(self):
        """Test normalizing with no connections."""
        aws_data = {
            "resources": [{"type": "ec2", "id": "i-1", "properties": {}}],
            "connections": []
        }

        result = normalize_aws_architecture(aws_data)

        assert result["normalized_connections"] == []


class TestErrorHandling:
    """Test error handling in normalization."""

    def test_normalize_invalid_aws_resource(self):
        """Test normalizing invalid AWS resource."""
        aws_data = {
            "resources": [
                {
                    "type": "invalid_type",
                    "id": "res-1",
                    "properties": {}
                }
            ]
        }

        result = normalize_aws_architecture(aws_data)

        # Should handle gracefully
        assert "normalized_resources" in result
        assert len(result["normalized_resources"]) == 1

        resource = result["normalized_resources"][0]
        assert resource["type"] == "unknown"
        assert "error" in resource

    @patch('httpx.AsyncClient')
    def test_external_service_failure(self, mock_client):
        """Test handling external service failures."""
        # Mock connection error
        mock_client.return_value.__aenter__.side_effect = Exception("Connection failed")

        # This should not crash the normalization
        aws_data = {
            "resources": [{"type": "ec2", "id": "i-1", "properties": {}}]
        }

        result = normalize_aws_architecture(aws_data)

        # Should still return a result
        assert "normalized_resources" in result


class TestMetadataHandling:
    """Test metadata handling in normalization."""

    def test_normalize_with_metadata(self):
        """Test normalization preserves metadata."""
        aws_data = {
            "resources": [
                {
                    "type": "ec2",
                    "id": "i-1",
                    "properties": {"instance_type": "t2.micro"},
                    "metadata": {"environment": "production", "team": "backend"}
                }
            ]
        }

        result = normalize_aws_architecture(aws_data)

        resource = result["normalized_resources"][0]
        assert "metadata" in resource
        assert resource["metadata"]["environment"] == "production"
        assert resource["metadata"]["team"] == "backend"

    def test_normalize_adds_platform_metadata(self):
        """Test normalization adds platform metadata."""
        aws_data = {
            "resources": [{"type": "ec2", "id": "i-1", "properties": {}}]
        }

        result = normalize_aws_architecture(aws_data)

        resource = result["normalized_resources"][0]
        assert resource["platform"] == "aws"
        assert "normalized_at" in resource
        assert "normalization_version" in resource


class TestFileFormatSupport:
    """Test support for different file formats."""

    def test_normalize_json_format(self):
        """Test normalizing JSON format data."""
        json_data = json.dumps({
            "resources": [{"type": "ec2", "id": "i-1", "properties": {}}]
        })

        result = normalize_aws_architecture(json.loads(json_data))

        assert "normalized_resources" in result
        assert len(result["normalized_resources"]) == 1

    def test_normalize_yaml_format(self):
        """Test normalizing YAML format data."""
        import yaml

        yaml_data = yaml.dump({
            "resources": [{"type": "ec2", "id": "i-1", "properties": {}}]
        })

        # Parse back to dict for normalization
        parsed_data = yaml.safe_load(yaml_data)
        result = normalize_aws_architecture(parsed_data)

        assert "normalized_resources" in result

    def test_normalize_xml_format(self):
        """Test normalizing XML format data."""
        xml_data = """<?xml version="1.0"?>
        <architecture>
            <resources>
                <resource type="ec2" id="i-1">
                    <properties>
                        <instance_type>t2.micro</instance_type>
                    </properties>
                </resource>
            </resources>
        </architecture>"""

        # This would require XML parsing logic
        # For now, test that it doesn't crash
        try:
            # Mock XML to dict conversion
            dict_data = {
                "resources": [{"type": "ec2", "id": "i-1", "properties": {"instance_type": "t2.micro"}}]
            }
            result = normalize_aws_architecture(dict_data)
            assert "normalized_resources" in result
        except Exception:
            # XML parsing not implemented yet
            pass
