# Observability Plan

## Overview
Observability in AI Dev OS provides insights into system behavior, performance, and health through structured logging, metrics, and tracing capabilities.

## Logging

### Structured Logging
All components use JSON-formatted structured logging for consistent parsing and analysis.

#### Log Format
```json
{
  "timestamp": "2026-04-05T10:30:00Z",
  "level": "INFO",
  "component": "core.orchestrator",
  "action": "workflow_start",
  "message": "Starting AI Dev OS workflow",
  "fields": {
    "workflow_id": "wf_12345",
    "user_request": "build a web scraper",
    "status": "initiated"
  }
}
```

### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational information
- **WARNING**: Potentially harmful situations
- **ERROR**: Error events that might still allow continuation
- **CRITICAL**: Severe errors that may prevent continuation

### Implementation
- Uses `python-json-logger` for JSON formatting
- Centralized logger configuration in `ai_dev_os.utils.logging`
- Component-specific loggers for traceability

## Metrics

### Core Metrics
AI Dev OS tracks key performance indicators through Prometheus-compatible metrics:

#### Workflow Metrics
- `ai_dev_os_workflows_total`: Total workflows initiated
- `ai_dev_os_workflows_success_total`: Successful workflows
- `ai_dev_os_workflows_failed_total`: Failed workflows
- `ai_dev_os_workflow_duration_seconds`: Workflow execution time histogram

#### Agent Metrics
- `ai_dev_os_agent_tasks_total`: Total agent tasks processed
- `ai_dev_os_agent_task_duration_seconds`: Agent task execution time
- `ai_dev_os_agent_errors_total`: Agent errors by type

#### Integration Metrics
- `ai_dev_os_integration_calls_total`: External API calls by service
- `ai_dev_os_integration_call_duration_seconds`: API call latency
- `ai_dev_os_integration_errors_total`: Integration errors by service

#### System Metrics
- `ai_dev_os_active_sandboxes`: Currently running sandboxes
- `ai_dev_os_memory_usage_bytes`: Memory consumption
- `ai_dev_os_cpu_utilization`: CPU usage percentage

### Implementation
- Uses `prometheus-client` for metric exposition
- Metrics endpoints available at `/metrics` when enabled
- Automatic instrumentation of key operations

## Tracing (Future Enhancement)

### OpenTelemetry Integration
Planned implementation for distributed tracing:
- Trace context propagation across components
- Span creation for key operations
- Export to tracing backends (Jaeger, Zipkin, etc.)
- Correlation of logs with traces

### Current Status
Tracing instrumentation is planned for Phase B/C implementation.
Core logging and metrics provide immediate observability value.

## Health Checks

### Liveness Probe
Indicates if the application is running:
- Basic process health
- Critical service connectivity

### Readiness Probe
Indicates if the application is ready to serve requests:
- All dependencies available
- Sandbox runtime initialized
- Integrations configured

### Implementation
Health check endpoints available at `/health` and `/ready` when web interface is enabled.

## Configuration

### Environment Variables
- `AI_DEV_OS_LOG_LEVEL`: Default log level (INFO)
- `AI_DEV_OS_METRICS_ENABLED`: Enable/disable metrics endpoint (false)
- `AI_DEV_OS_METRICS_PORT`: Port for metrics endpoint (9090)
- `AI_DEV_OS_LOG_FORMAT`: Log format (json)

### Runtime Configuration
- Logging level adjustable at runtime
- Metrics collection toggleable per component
- Sampling rates for high-volume operations

## Best Practices

### Log Content
- Never log secrets or sensitive data
- Include correlation IDs for request tracing
- Use consistent field names across components
- Provide actionable information in log messages

### Metric Design
- Use meaningful metric names with clear units
- Label metrics appropriately for dimensional analysis
- Avoid high-cardinality labels that could explode series count
- Document all metrics in the metrics registry

### Alerting Guidelines
- Alert on symptoms, not just causes
- Ensure alerts are actionable and have clear runbooks
- Balance signal-to-noise ratio to prevent alert fatigue
- Test alerting rules regularly

## Implementation Roadmap

### Phase A (Current)
- Structured JSON logging foundation
- Basic metrics instrumentation for core workflows
- Health check endpoints planned

### Phase B
- Enhanced metrics for integrations and sandboxes
- Alerting rules for critical failure modes
- Initial tracing prototypes

### Phase C
- Full OpenTelemetry tracing integration
- Distributed trace correlation with logs
- Advanced dashboard and visualization options

## Usage Examples

### Adding Logging to a Component
```python
import logging
from ai_dev_os.utils.logging import get_logger

logger = get_logger(__name__)

def process_workflow(workflow_id):
    logger.info("Processing workflow", 
                extra={"fields": {"workflow_id": workflow_id, "status": "started"}})
    # ... processing logic ...
    logger.info("Workflow completed", 
                extra={"fields": {"workflow_id": workflow_id, "status": "completed"}})
```

### Adding Metrics
```python
from prometheus_client import Counter, Histogram
from ai_dev_os.utils.metrics import get_meter

WORKFLOW_COUNTER = Counter(
    'ai_dev_os_workflows_total',
    'Total workflows processed',
    ['status']
)

def execute_workflow():
    try:
        # ... workflow logic ...
        WORKFLOW_COUNTER.labels(status='success').inc()
    except Exception:
        WORKFLOW_COUNTER.labels(status='failed').inc()
        raise
```

## Monitoring Integrations

### External Service Monitoring
Each integration tracks:
- Call volume and success rates
- Latency distributions
- Error patterns and retry behavior
- Rate limiting incidents

### Dashboard Integration
Metrics designed to work with:
- Grafana dashboards
- Prometheus alerting rules
- Custom monitoring solutions
- Built-in HUD status displays

## Security Considerations

### Log Sanitization
- Automatic redaction of known secret patterns
- Field-level filtering for sensitive data
- Audit logging for access to sensitive operations

### Metric Exposure
- Metrics endpoint accessible only on internal networks by default
- Authentication optional for internal use
- Rate limiting to prevent abuse

## Troubleshooting

### Common Issues
1. **Missing logs**: Check logger configuration and level settings
2. **No metrics**: Verify metrics endpoint is enabled and accessible
3. **High cardinality**: Review label usage in metrics
4. **Performance impact**: Adjust sampling rates if needed

### Debugging Tips
- Enable DEBUG logging temporarily for troubleshooting
- Use correlation IDs to trace requests across components
- Check metric labels for unexpected variations
- Verify environment configuration for observability features

## Maintenance

### Log Rotation
- Handled by external log aggregation systems
- Local development uses rotating file handlers if needed
- Production relies on centralized log management

### Metric Retention
- Configured in Prometheus or compatible storage
- Retention policies aligned with business requirements
- Downsampling strategies for long-term trends

## References
- Structured logging best practices
- Prometheus metrics naming conventions
- OpenTelemetry semantic conventions
- Observability patterns for distributed systems