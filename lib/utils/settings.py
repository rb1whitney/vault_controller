import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml


@dataclass
class ClusterConfig:
    api_url: str
    api_port: int = 8200
    api_protocol: str = "https"
    servers: List[str] = None
    config_env: Optional[str] = None
    key_holders: List[str] = None
    key_threshold: int = 1
    key_encrypt: bool = False
    recovery_key: bool = False

    def __post_init__(self):
        if self.servers is None:
            self.servers = []
        if self.key_holders is None:
            self.key_holders = []

    @property
    def api_endpoint(self) -> str:
        return f"{self.api_protocol}://{self.api_url}:{self.api_port}"
    
    @property
    def server_endpoints(self) -> List[str]:
        return [f"{self.api_protocol}://{s}:{self.api_port}" for s in self.servers]
    
    @property
    def dr_endpoint(self) -> str:
        return f"{self.api_protocol}://{self.api_url}:8201"

class VaultSettings:
    def __init__(self, clusters: Dict[str, ClusterConfig]):
        self.clusters = clusters

    @classmethod
    def load(cls, path: Optional[str] = None):
        if not path:
            path = os.path.join(os.path.dirname(__file__), "../../config/contexts.yaml")
        
        with open(path) as f:
            data = yaml.safe_load(f)
        
        clusters = {}
        for name, config in data.get("clusters", {}).items():
            clusters[name] = ClusterConfig(**config)
        return cls(clusters=clusters)

def get_cluster(name: str) -> ClusterConfig:
    settings = VaultSettings.load()
    if name not in settings.clusters:
        raise ValueError(f"Cluster '{name}' not found in configuration.")
    return settings.clusters[name]
