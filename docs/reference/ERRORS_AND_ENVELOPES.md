# Errors and Envelopes

## Success envelope
```json
{
  "success": true,
  "data": { /* payload */ },
  "message": "optional",
  "request_id": "abc-123"
}
```

## Error envelope
```json
{
  "success": false,
  "error_code": "ANALYSIS_FAILED",
  "details": { /* context */ },
  "request_id": "abc-123"
}
```

## Common error codes
- ANALYSIS_FAILED
- REPORT_GENERATION_FAILED
- VALIDATION_ERROR
- SERVICE_UNAVAILABLE
- NATURAL_LANGUAGE_ANALYSIS_FAILED

## HTTP and FastAPI behavior
- 422 for malformed JSON at request parsing time
- 400 for explicit validation failures
- 5xx for server errors (surfaces with error envelope when handled)
