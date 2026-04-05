# Data Contracts

## Overview
Data contracts in AI Dev OS define the schema, validation rules, and serialization formats for data exchanged between components. These contracts ensure type safety, backward compatibility, and clear interfaces.

## Core Data Models

### WorkflowRequest
Represents a user request entering the system.

```python
class WorkflowRequest(BaseModel):
    request_id: str = Field(..., description="Unique identifier for the request")
    user_id: str = Field(..., description="Identifier of the requesting user")
    prompt: str = Field(..., min_length=1, description="The user's request/prompt")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    priority: WorkflowPriority = Field(default=WorkflowPriority.NORMAL, description="Request priority")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### WorkflowResponse
Represents the result of a completed workflow.

```python
class WorkflowResponse(BaseModel):
    request_id: str = Field(..., description="Identifier of the original request")
    status: WorkflowStatus = Field(..., description="Final status of the workflow")
    result: Optional[Dict[str, Any]] = Field(None, description="Workflow output/artifacts")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="Workflow start time")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion time")
    metrics: WorkflowMetrics = Field(default_factory=WorkflowMetrics, description="Execution metrics")
```

### AgentTask
Represents a unit of work assigned to an agent.

```python
class AgentTask(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    task_type: TaskType = Field(..., description="Type of task (code, train, sim, etc.)")
    payload: Dict[str, Any] = Field(..., description="Task-specific input data")
    dependencies: List[str] = Field(default_factory=list, description="Prerequisite task IDs")
    timeout_seconds: int = Field(default=300, description="Task timeout in seconds")
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy, description="Retry configuration")
```

### SandboxConfig
Configuration for sandbox execution environments.

```python
class SandboxConfig(BaseModel):
    sandbox_type: SandboxType = Field(..., description="Type of sandbox (modal, docker, etc.)")
    resource_limits: ResourceLimits = Field(..., description="CPU, memory, disk limits")
    environment_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    volume_mounts: List[VolumeMount] = Field(default_factory=list, description="File system mounts")
    network_policy: NetworkPolicy = Field(default_factory=NetworkPolicy, description="Network access rules")
```

## Validation Rules

### Request Validation
- All incoming requests must have a non-empty prompt
- Request IDs must be unique and follow UUID format
- User IDs must conform to authentication system format
- Context data must be JSON-serializable

### Response Validation
- Workflow responses must have a valid status
- Successful workflows must contain result data
- Failed workflows must contain error information
- Timestamps must be in ISO 8601 format

### Agent Task Validation
- Task payloads must conform to task-type specific schemas
- Dependencies must reference existing tasks in the workflow
- Timeout values must be positive integers
- Retry policies must be valid configurations

## Serialization

### Primary Format
JSON is the primary serialization format for all data contracts.

### Alternative Formats
- MessagePack for high-performance internal communication
- Protobuf for external API definitions (planned)
- YAML for configuration files

### Compatibility
- All contracts must maintain backward compatibility
- Breaking changes require major version bump
- Deprecation warnings for removed fields
- Version field included in all serialized data

## Error Handling

### ErrorResponse
Standard error format for all API endpoints and internal communications.

```python
class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    request_id: Optional[str] = Field(None, description="Associated request ID if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Error Codes
- VALIDATION_ERROR: Invalid input data
- AUTHENTICATION_ERROR: Missing or invalid credentials
- AUTHORIZATION_ERROR: Insufficient permissions
- RESOURCE_NOT_FOUND: Requested resource does not exist
- INTERNAL_ERROR: Unexpected system error
- EXTERNAL_SERVICE_ERROR: Failure in external dependency
- TIMEOUT_ERROR: Operation exceeded time limit
- RATE_LIMIT_ERROR: Rate limit exceeded

## Implementation Guidelines

### Using Pydantic
All data contracts should be defined using Pydantic models for automatic validation and serialization.

### Version Inclusion
Include a `version` field in all major data structures to track contract evolution.

### Documentation
Each contract should be documented with:
- Field descriptions and constraints
- Example values
- Usage notes
- Version history

### Testing
- Property-based testing for contract validation
- Fuzzing for edge cases in input handling
- Contract tests between components
- Schema validation tests

## Evolution Strategy

### Backward Compatibility
- New fields should be optional with sensible defaults
- Removed fields should be deprecated before removal
- Type changes should maintain semantic compatibility
- Enum additions should be safe (new values only)

### Breaking Changes
- Require major version increment
- Provide migration guides
- Maintain deprecated versions for transition period
- Communicate changes well in advance

## Examples

### Valid WorkflowRequest
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "prompt": "Create a REST API for user management",
  "context": {
    "language": "python",
    "framework": "fastapi"
  },
  "priority": "high",
  "created_at": "2026-04-05T10:30:00Z"
}
```

### Valid WorkflowResponse
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "files_created": ["main.py", "models.py", "routes.py"],
    "lines_of_code": 245,
    "tests_passed": 12
  },
  "error": null,
  "started_at": "2026-04-05T10:30:05Z",
  "completed_at": "2026-04-05T10:35:22Z",
  "metrics": {
    "total_tokens": 15000,
    "cost_estimate": 0.045,
    "agent_utilization": 0.78
  }
}
```

## Validation Implementation

### Automatic Validation
- Pydantic validates on model instantiation
- Custom validators for complex constraints
- Root validators for cross-field validation

### Manual Validation Points
- API entry points validate incoming requests
- Service boundaries validate outgoing responses
- Internal component interfaces validate exchanged data
- Persistence layer validates stored data

## Contract Testing

### Consumer-Driven Contracts
- Define expectations from service consumers
- Verify providers meet those expectations
- Automated testing in CI pipeline

### Schema Registry
- Planned implementation for contract versioning
- Compatibility checking between versions
- Schema evolution tracking

## References
- API design best practices
- Protobuf and JSON Schema comparison
- Pydantic documentation and examples
- Contract testing patterns (Pact, Spring Cloud Contract)