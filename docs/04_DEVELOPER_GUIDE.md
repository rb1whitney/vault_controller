# Developer Guide

This guide provides the technical specifications for extending the Vault controller. Developers must adhere to the modular library structure and strictly enforce the single-responsibility principle across all transport and validation layers.

---

## Content

- [Architectural Separation Matrix](#architectural-separation-matrix)
- [Module Design Patterns & API Anatomy](#module-design-patterns--api-anatomy)
- [Deterministic Integration Testing](#deterministic-integration-testing)
- [Operational Safety Guardrails](#operational-safety-guardrails)

---

## Architectural Separation Matrix

The codebase is partitioned into executable entrypoints and stateless domain mechanics.

```bash
projects/vault/
├── bin/                       <── Entrypoints (thin controllers)
│   ├── cluster_secret_data.py
│   ├── cluster_ops.py
│   └── cluster_encrypt_ops.py
├── lib/                       <── Domain Mechanics (stateless logic)
│   ├── core/
│   │   ├── auth.py            <── Unified Auth negotiation
│   │   └── client.py          <── HTTP transport & base methods
│   ├── engines/
│   │   ├── manager.py         <── Engine orchestration
│   │   ├── kv.py              <── KV backend logic
│   │   └── transit.py         <── Cryptographic operations
│   ├── validation/
│   │   └── schema.py          <── YAML schema enforcement
│   └── utils/
│       ├── http.py            <── Resiliency wrappers
│       └── logging.py         <── Standardized telemetry
└── tests/                     <── Pytest suite
    └── integration/
        └── test_reconciliation.py
```

### 1. Execution Boundary (`bin/`)
Scripts in `bin/` manage environment context and coordinate system streams. They must not contain raw HTTP logic or complex data parsing.

### 2. Domain Mechanics Layer (`lib/`)
Business logic resides within the `projects.vault.lib` namespace. Modules are decoupled by functionality (core transport, engine specific logic, validation, and utilities).

---

## Module Design Patterns & API Anatomy

### 1. Transport Core: `projects.vault.lib.core.client.VaultClient`
Encapsulates session state and outbound mutations.

```python
from projects.vault.lib.core.client import VaultClient

# Initialization via Unified Auth
client = VaultClient(
    addr="http://localhost:8200",
    auth_type="token",
    principal="admin",
    secret="hvs.root"
)

# Deterministic GET operation
response = client.get("sys/mounts")
```

### 2. Schema Validation: `projects.vault.lib.validation.schema.SchemaValidator`
Enforces structural integrity of YAML manifests before network execution.

```python
import yaml
from projects.vault.lib.validation.schema import SchemaValidator

validator = SchemaValidator()
with open("blueprint.yaml", "r") as f:
    config = yaml.safe_load(f)

# Raises ValidationError on structural failure
validator.validate(config)
```

---

## Deterministic Integration Testing

Verification is enforced through `pytest`. The suite utilizes local ephemeral `example_vault` containers to validate configurations in isolation.

```python
import pytest
from projects.vault.lib.core.client import VaultClient
from projects.vault.lib.engines.manager import EngineManager

@pytest.fixture
def vault_client():
    return VaultClient("http://localhost:8200", "token", secret="root")

def test_engine_idempotency(vault_client):
    manager = EngineManager(vault_client)
    payload = {"path": "kv-dev", "type": "kv"}
    
    # First pass: Create
    manager.reconcile_engines([payload])
    
    # Second pass: No-op (Idempotency check)
    result = manager.reconcile_engines([payload])
    assert result.modified is False
```

Run the suite:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest projects/vault/tests/
```

---

## Operational Safety Guardrails

- **Explicit Timeouts**: All network calls must implement a 10s timeout via `projects.vault.lib.utils.http`.
- **Statelessness**: No local state files are permitted. The cluster is the only source of truth.
- **Error Propagation**: Low-level API errors must be wrapped in domain-specific exceptions (e.g., `VaultAPIError`) to assist with debugging.

---
**Navigation**
- [Introduction](01_VAULT_INTRODUCTION.md)
- [Admin Guide](02_ADMIN_GUIDE.md)
- [User Workflows](03_USER_WORKFLOWS.md)
