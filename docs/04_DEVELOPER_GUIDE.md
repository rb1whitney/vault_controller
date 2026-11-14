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
├── bin/                       <── Consolidated CLI Entrypoint
│   └── vault_ctl.py           <── Main Typer CLI
├── lib/                       <── Domain Mechanics (stateless logic)
│   ├── core/
│   │   ├── hvac_client.py     <── hvac.Client wrapper
│   │   ├── adapter.py         <── Legacy adapter for backward compatibility
│   │   └── client.py          <── High-level client orchestrator
│   ├── auth/
│   │   ├── factory.py         <── Auth strategy factory
│   │   ├── standard.py        <── Token, LDAP, AppRole (hvac)
│   │   └── cloud.py           <── AWS, GCP (hvac)
│   ├── engines/
│   │   └── payload_processor.py <── Transit & KV-V2 logic (hvac)
│   ├── validation/
│   │   ├── models.py          <── Pydantic data models
│   │   └── manager.py         <── Validation orchestrator
│   └── utils/
│       ├── settings.py        <── Dataclass-based config loader
│       └── ops.py             <── High-level cluster operations
└── tests/                     <── Pytest suite
    ├── test_integration.py    <── Full-lifecycle reconciliation
    └── test_auth_strategies.py <── Mocked hvac auth flows
```

### 1. Execution Boundary (`bin/`)
The `vault_ctl.py` CLI uses **Typer** to coordinate subcommands (`cluster`, `secrets`). It translates user input into calls to `lib/utils/ops.py` or directly initializes library components.

### 2. Domain Mechanics Layer (`lib/`)
Business logic is decoupled into specific domain modules:
- **`lib/core`**: Low-level transport using the official `hvac` library.
- **`lib/auth`**: Pluggable authentication strategies leveraging `hvac` native methods.
- **`lib/validation`**: Declarative schema and business rule enforcement using **Pydantic**.
- **`lib/engines`**: Logic for secret engines (Transit decryption, KV management).

---

## Module Design Patterns & API Anatomy

### 1. Transport Core: `lib.core.client.LocalVaultClient`
Encapsulates session state and outbound mutations. Now exposes the underlying `hvac_client`.

```python
from lib.core.client import LocalVaultClient
import logging

logger = logging.getLogger("dev")
client = LocalVaultClient("http://localhost:8200", logger)

# Authentication via Strategy Factory
client.login(auth_method="token")

# Access native hvac methods
health = client.hvac_client.sys.read_health_status()
```

### 2. Pydantic Validation: `lib.validation.models.VaultPayload`
Enforces structural integrity and complex business rules (e.g., TTL limits) using typed models.

```python
from lib.validation.models import VaultPayload

data = {"_namespace": "test", "api_paths": [...]}
# Automatic validation on instantiation
payload = VaultPayload(**data) 
```

---

## Deterministic Integration Testing

Verification is enforced through `pytest`. The suite utilizes a local ephemeral `vault server -dev` process.

```python
import pytest
from lib.core.client import VaultClient
from lib.engines.manager import EngineManager

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

- **Explicit Timeouts**: All network calls must implement a 10s timeout via `lib.utils.http`.
- **Statelessness**: No local state files are permitted. The cluster is the only source of truth.
- **Error Propagation**: Low-level API errors must be wrapped in domain-specific exceptions (e.g., `VaultAPIError`) to assist with debugging.

---
**Navigation**
- [Introduction](01_VAULT_INTRODUCTION.md)
- [Admin Guide](02_ADMIN_GUIDE.md)
- [User Workflows](03_USER_WORKFLOWS.md)
