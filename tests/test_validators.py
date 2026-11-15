import pytest

from lib.validation.models import (
    validate_cluster_name,
    validate_namespace,
    validate_path,
)


def test_validate_cluster_name_valid():
    assert validate_cluster_name("prod-cluster_01") == "prod-cluster_01"

def test_validate_cluster_name_invalid():
    with pytest.raises(ValueError):
        validate_cluster_name("prod cluster!")

def test_validate_namespace_valid():
    assert validate_namespace("my-namespace_123") == "my-namespace_123"

def test_validate_namespace_invalid():
    with pytest.raises(ValueError):
        validate_namespace("namespace/path")

def test_validate_path_valid():
    assert validate_path("secret/my-path_01") == "secret/my-path_01"
    assert validate_path("/secret/path/") == "/secret/path/"

def test_validate_path_invalid_traversal():
    with pytest.raises(ValueError):
        validate_path("../../etc/passwd")

def test_validate_path_invalid_format():
    with pytest.raises(ValueError):
        validate_path("secret//path")
