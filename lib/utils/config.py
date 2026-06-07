import os

import yaml


def get_cluster_config(cluster_name):
    """
    Loads cluster-specific metadata from contexts.yaml.
    Standardizes endpoints and protocols.
    """
    current_dir = os.path.dirname(__file__)
    config_path = os.path.join(current_dir, "../../config/contexts.yaml")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if cluster_name not in config.get("clusters", {}):
        raise NameError(f"Cluster '{cluster_name}' not found in configuration.")

    cluster = config["clusters"][cluster_name]
    protocol = cluster.get("api_protocol", "https")
    port = cluster["api_port"]
    host = cluster["api_url"]

    # Pre-calculate common endpoints
    cluster["server_endpoints"] = [
        f"{protocol}://{s}:{port}" for s in cluster["servers"]
    ]
    cluster["api_endpoint"] = f"{protocol}://{host}:{port}"
    cluster["dr_endpoint"] = f"{protocol}://{host}:8201"

    return cluster
