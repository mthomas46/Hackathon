# 📊 Comprehensive Analysis Results Report

**Report Generated:** 2025-09-19 09:45:23 UTC
**Service:** Summarizer Hub Service
**Format:** Comprehensive Analysis Report

---

- **Success:** ✅ Yes
## Batch Info

  - **Total Requested:** 33
  - **Total Processed:** 33
  - **Successful:** 33
  - **Failed:** 0

- **Total Documents:** 33
- **Processed Documents:** 33
- **Processing Time:** 0
## Document Summaries

  ### Document Summaries Details

  #### Item 1

    - **Document Id:** conf_architecture_17582931_0
    - **Title:** Education Platform - System Architecture
    - **Category:** architecture
    ## Tags

      ### Tags Details

      1. architecture
      2. education
      3. svelte
      4. go

    - **Summary:** # Education Platform Architecture

## Overview
The education platform is built on microservices architecture for scalability and resilience.

## Core Components
- **User Management Service**: Handles authentication, SSO, and user profiles
- **Business Logic Engine**: Implements core education domain logic with robust validation
- **Data Processing Service**: Real-time analytics, ETL pipelines, and reporting
- **Notification Service**: Asynchronous event-driven notifications (email, SMS, webhooks)

## Technology Stack
- Frontend: Svelte (SPA, SSR, PWA support)
- Backend: Go (REST & GraphQL APIs)
- Database: PostgreSQL, Redis, S3
- Infrastructure: Docker, Kubernetes, Terraform, CI/CD

## Security
- OAuth2, RBAC, audit logging, encrypted secrets

## Scalability
- Horizontal scaling, autoscaling, load balancing

## Diagram
```
[Insert architecture diagram here]
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 2

    - **Document Id:** conf_api_17582931_1
    - **Title:** API Documentation - Education Service
    - **Category:** api
    ## Tags

      ### Tags Details

      1. api
      2. education
      3. svelte
      4. go

    - **Summary:** # Education Service API

## Overview
RESTful and GraphQL APIs for education platform operations.

## Authentication
All API requests require JWT token authentication and API key header.

## Endpoints
### GET /api/v1/education/items
Retrieves a list of education items.

**Response:**
```json
{
  "items": [
    {
      "id": "123",
      "name": "Sample Item",
      "status": "active"
    }
  ]
}
```

### POST /api/v1/education/items
Creates a new item.

**Request Body:**
```json
{
  "name": "New Item",
  "description": "Detailed description."
}
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 3

    - **Document Id:** conf_design_17582931_2
    - **Title:** Design Document - Education Notifications
    - **Category:** design
    ## Tags

      ### Tags Details

      1. design
      2. education
      3. svelte
      4. go

    - **Summary:** # Design Doc: Notification Service

## Purpose
Design for asynchronous, scalable notification delivery supporting email, SMS, and push.

## Requirements
- Pluggable provider architecture
- Guaranteed delivery and retry
- Idempotency
- Auditable logs

## Sequence Diagram
```
[Insert sequence diagram]
```

## Open Questions
- How to handle provider outages?
- SLA for delivery latency?

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 4

    - **Document Id:** conf_requirements_17582931_3
    - **Title:** Requirements Specification - Education Onboarding
    - **Category:** requirements
    ## Tags

      ### Tags Details

      1. requirements
      2. education
      3. svelte
      4. go

    - **Summary:** # Requirements: User Onboarding

## Functional
- Collect user info (name, email, org)
- Email verification
- Welcome tour

## Non-Functional
- Onboarding completion < 2 minutes
- Accessible (WCAG 2.1 AA)
- GDPR compliant

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 5

    - **Document Id:** conf_security_17582931_4
    - **Title:** Security Overview - Education Platform
    - **Category:** security
    ## Tags

      ### Tags Details

      1. security
      2. education
      3. svelte
      4. go

    - **Summary:** # Security Overview

## Threat Model
- External attackers
- Insider threats
- Data exfiltration

## Controls
- Encryption at rest/in transit
- RBAC, MFA, audit logs
- Regular penetration testing

## Incident Response
- 24/7 monitoring
- Runbooks

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 6

    - **Document Id:** conf_testing_17582931_5
    - **Title:** Testing Strategy - Education Platform
    - **Category:** testing
    ## Tags

      ### Tags Details

      1. testing
      2. education
      3. svelte
      4. go

    - **Summary:** # Testing Strategy

## Types
- Unit, integration, E2E, load, security

## Tooling
- Pytest, Cypress, Postman, Snyk

## Coverage
- 90%+ unit test coverage
- Automated regression suite

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 7

    - **Document Id:** conf_deployment_17582931_6
    - **Title:** Deployment Guide - Education Platform
    - **Category:** deployment
    ## Tags

      ### Tags Details

      1. deployment
      2. education
      3. svelte
      4. go

    - **Summary:** # Deployment Guide

## Environments
- Dev, Staging, Prod

## CI/CD
- GitHub Actions, ArgoCD, DockerHub

## Rollback
- Blue/green, canary
- Rollback steps

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 8

    - **Document Id:** jira_feature_17582931_0
    - **Title:** Implement Advanced Education Dashboard
    - **Category:** feature
    ## Tags

      ### Tags Details

      1. feature
      2. high
      3. jira
      4. education

    - **Summary:** As a product manager, I want an advanced dashboard so I can track education platform metrics.

## Acceptance Criteria
- Real-time metrics
- Svelte frontend
- Go backend API
- Mobile-responsive
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 9

    - **Document Id:** jira_bug_17582931_1
    - **Title:** Bug: Education API returns 500 on POST /items
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. critical
      3. jira
      4. education

    - **Summary:** Steps to Reproduce:
1. POST to /api/v1/education/items with invalid payload
2. Observe 500 error

## Expected
Graceful validation error (400)

## Actual
500 Internal Server Error

## Logs
```
[stacktrace]
```
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 10

    - **Document Id:** jira_feature_17582931_2
    - **Title:** Epic: Education Mobile App Launch
    - **Category:** feature
    ## Tags

      ### Tags Details

      1. feature
      2. high
      3. jira
      4. education

    - **Summary:** Epic to track all work for mobile app launch.

## Child Issues
- JIRA-123: Mobile UI
- JIRA-124: API integration
- JIRA-125: Push notifications
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 11

    - **Document Id:** jira_feature_17582931_3
    - **Title:** Task: Refactor Go Service Layer
    - **Category:** feature
    ## Tags

      ### Tags Details

      1. feature
      2. medium
      3. jira
      4. education

    - **Summary:** Refactor service layer for maintainability and testability.

## Subtasks
- Add unit tests
- Extract business logic
- Update documentation
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 12

    - **Document Id:** jira_user_story_17582931_4
    - **Title:** Story: As a user, I can reset my password via email
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. high
      3. jira
      4. education

    - **Summary:** User should be able to request password reset and receive a secure email link.

## Acceptance Criteria
- Email sent to user
- Link expires in 30 minutes
- Password complexity enforced
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 13

    - **Document Id:** pr_17582931_0
    - **Title:** PR: Education - Feature #696
    - **Category:** development
    ## Tags

      ### Tags Details

      1. pr
      2. github
      3. review
      4. education

    - **Summary:** ## Description
Implements bugfix for education module.

## Changes
- Updated API logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-725

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 14

    - **Document Id:** pr_17582931_1
    - **Title:** PR: Education - Bugfix #821
    - **Category:** development
    ## Tags

      ### Tags Details

      1. pr
      2. github
      3. review
      4. education

    - **Summary:** ## Description
Implements feature for education module.

## Changes
- Updated database logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-678

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 15

    - **Document Id:** pr_17582931_2
    - **Title:** PR: Education - Feature #639
    - **Category:** development
    ## Tags

      ### Tags Details

      1. pr
      2. github
      3. review
      4. education

    - **Summary:** ## Description
Implements refactor for education module.

## Changes
- Updated authentication logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-552

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 16

    - **Document Id:** story_17582931_0
    - **Title:** User Story: As a user...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. svelte

    - **Summary:** As a developer, I want to reset password so that I can get timely alerts.

## Acceptance Criteria
- Secure reset
- Mobile support

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 17

    - **Document Id:** story_17582931_1
    - **Title:** User Story: As an admin...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. svelte

    - **Summary:** As a admin, I want to export data so that I can get timely alerts.

## Acceptance Criteria
- Email notifications
- Audit logs

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 18

    - **Document Id:** story_17582931_2
    - **Title:** User Story: As a user...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. svelte

    - **Summary:** As a user, I want to customize dashboard so that I can get timely alerts.

## Acceptance Criteria
- Export as CSV
- Audit logs

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 19

    - **Document Id:** rfc_17582931_0
    - **Title:** RFC: Migrate to Kubernetes
    - **Category:** rfc
    ## Tags

      ### Tags Details

      1. rfc
      2. proposal
      3. education

    - **Summary:** # RFC: Migrate to Kubernetes

## Motivation
Enhance scalability

## Proposal
- Migrate deployment to Kubernetes
- Update documentation
- Provide migration plan

## Drawbacks
- Learning curve

## Alternatives
- Keep current approach
- Evaluate other tools

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 20

    - **Document Id:** rfc_17582931_1
    - **Title:** RFC: Switch to GraphQL
    - **Category:** rfc
    ## Tags

      ### Tags Details

      1. rfc
      2. proposal
      3. education

    - **Summary:** # RFC: Migrate to Kubernetes

## Motivation
Standardize API schema

## Proposal
- Switch REST to GraphQL
- Update documentation
- Provide migration plan

## Drawbacks
- Compatibility issues

## Alternatives
- Keep current approach
- Evaluate other tools

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 21

    - **Document Id:** meeting_17582931_0
    - **Title:** Meeting Notes: Sprint Planning
    - **Category:** meeting_notes
    ## Tags

      ### Tags Details

      1. meeting
      2. notes
      3. education

    - **Summary:** # Meeting Notes

**Date:** 2025-09-10T13:05:23.005478
**Attendees:** Sarah Johnson, Lisa Rodriguez, Priya Patel, Alex Thompson

## Agenda
- Review sprint goals
- Q&A

## Notes
- Identified key technical debt
- Schedule security review

## Action Items
- Prepare demo

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 22

    - **Document Id:** meeting_17582931_1
    - **Title:** Meeting Notes: Sprint Planning
    - **Category:** meeting_notes
    ## Tags

      ### Tags Details

      1. meeting
      2. notes
      3. education

    - **Summary:** # Meeting Notes

**Date:** 2025-09-11T08:22:23.005478
**Attendees:** Lisa Rodriguez, John Doe, David Kim, Alex Thompson

## Agenda
- Review sprint goals
- Architecture discussion

## Notes
- Identified key technical debt
- Follow up with DevOps

## Action Items
- Fix critical bug

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 23

    - **Document Id:** testplan_17582931_0
    - **Title:** Test Plan: Education Authentication
    - **Category:** testing
    ## Tags

      ### Tags Details

      1. test
      2. plan
      3. education

    - **Summary:** # Test Plan

## Scope
- API module

## Objectives
- Validate access control

## Test Cases
- Login with valid/invalid credentials
- Error messages

## Tooling
- Pytest

## Exit Criteria
- 100% test pass

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 24

    - **Document Id:** testplan_17582931_1
    - **Title:** Test Plan: Education UI
    - **Category:** testing
    ## Tags

      ### Tags Details

      1. test
      2. plan
      3. education

    - **Summary:** # Test Plan

## Scope
- UI module

## Objectives
- Validate login

## Test Cases
- API returns correct status codes
- Session timeout

## Tooling
- Cypress

## Exit Criteria
- 100% test pass

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 25

    - **Document Id:** deploy_17582931_0
    - **Title:** Deployment Guide: Education Dev
    - **Category:** deployment
    ## Tags

      ### Tags Details

      1. deploy
      2. guide
      3. education

    - **Summary:** # Deployment Guide

## Environment
- Staging

## Steps
- Build Docker image
- Push to registry
- Deploy with ArgoCD
- Run smoke tests

## Rollback
- Rollback to previous release
- Notify stakeholders

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 26

    - **Document Id:** deploy_17582931_1
    - **Title:** Deployment Guide: Education Dev
    - **Category:** deployment
    ## Tags

      ### Tags Details

      1. deploy
      2. guide
      3. education

    - **Summary:** # Deployment Guide

## Environment
- Production

## Steps
- Build Docker image
- Push to registry
- Deploy with ArgoCD
- Run smoke tests

## Rollback
- Rollback to previous release
- Notify stakeholders

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 27

    - **Document Id:** bug_17582931_0
    - **Title:** Bug: Education - UI crash
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. jira
      3. education

    - **Summary:** Steps to Reproduce:
1. Navigate to dashboard
2. Observe error

## Expected
Graceful error message

## Actual
UI freezes

## Logs
```
[stacktrace]
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 28

    - **Document Id:** bug_17582931_1
    - **Title:** Bug: Education - UI crash
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. jira
      3. education

    - **Summary:** Steps to Reproduce:
1. Login with invalid credentials
2. Observe error

## Expected
Graceful error message

## Actual
500 Internal Server Error

## Logs
```
[stacktrace]
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 29

    - **Document Id:** bug_17582931_2
    - **Title:** Bug: Education - Timeout error
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. jira
      3. education

    - **Summary:** Steps to Reproduce:
1. Navigate to dashboard
2. Observe error

## Expected
Graceful error message

## Actual
500 Internal Server Error

## Logs
```
[stacktrace]
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 30

    - **Document Id:** api_17582931_0
    - **Title:** API Documentation - Education Endpoint 2
    - **Category:** api
    ## Tags

      ### Tags Details

      1. api
      2. documentation
      3. rest
      4. education

    - **Summary:** # API Endpoint 2

## Method
DELETE /api/v1/education/endpoint2

## Description
Retrieves an entity.

## Request/Response
```json
{ "id": "abc0", "result": "ok" }
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 31

    - **Document Id:** api_17582931_1
    - **Title:** API Documentation - Education Endpoint 3
    - **Category:** api
    ## Tags

      ### Tags Details

      1. api
      2. documentation
      3. rest
      4. education

    - **Summary:** # API Endpoint 3

## Method
DELETE /api/v1/education/endpoint3

## Description
Updates an entity.

## Request/Response
```json
{ "id": "abc1", "result": "ok" }
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 32

    - **Document Id:** story_17582931_3
    - **Title:** User Story: As a user, I can change settings
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. svelte

    - **Summary:** As a user, I want to change settings so that I can customize experience.

## Acceptance Criteria
- Email alerts
- Auditable

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 33

    - **Document Id:** story_17582931_4
    - **Title:** User Story: As a user, I can receive alerts
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. svelte

    - **Summary:** As a user, I want to change settings so that I can customize experience.

## Acceptance Criteria
- Email alerts
- Accessible

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0


## Multi Document Analysis

  ## Categories Found

    ### Categories Found Details

    1. deployment
    2. development
    3. api
    4. design
    5. user_story
    6. meeting_notes
    7. feature
    8. security
    9. architecture
    10. requirements
    11. bug
    12. rfc
    13. testing

  - **Total Tags:** 30
  ## Document Distribution

    ## By Category

      - **Architecture:** 1
      - **Api:** 3
      - **Design:** 1
      - **Requirements:** 1
      - **Security:** 1
      - **Testing:** 3
      - **Deployment:** 3
      - **Feature:** 3
      - **Bug:** 4
      - **User Story:** 6
      - **Development:** 3
      - **Rfc:** 2
      - **Meeting Notes:** 2

    ## By Tag

      - **Architecture:** 1
      - **Education:** 33
      - **Svelte:** 12
      - **Go:** 7
      - **Api:** 3
      - **Design:** 1
      - **Requirements:** 1
      - **Security:** 1
      - **Testing:** 1
      - **Deployment:** 1
      - **Feature:** 3
      - **High:** 3
      - **Jira:** 8
      - **Bug:** 4
      - **Critical:** 1
      - **Medium:** 1
      - **User Story:** 6
      - **Pr:** 3
      - **Github:** 3
      - **Review:** 3
      - **Rfc:** 2
      - **Proposal:** 2
      - **Meeting:** 2
      - **Notes:** 2
      - **Test:** 2
      - **Plan:** 2
      - **Deploy:** 2
      - **Guide:** 2
      - **Documentation:** 2
      - **Rest:** 2

    - **Total Categories:** 13
    - **Total Tags:** 30

  ## Cross Document Insights

    ## Similarity Patterns

      ### Similarity Patterns Details

      #### Item 1

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. conf_api_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 2

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. conf_design_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 3

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. conf_requirements_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 4

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. conf_security_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 5

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. conf_testing_17582931_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 6

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. conf_deployment_17582931_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 7

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. story_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 8

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 9

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 10

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 11

        ## Documents

          ### Documents Details

          1. conf_architecture_17582931_0
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 12

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. conf_design_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 13

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. conf_requirements_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 14

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. conf_security_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 15

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. conf_testing_17582931_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 16

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. conf_deployment_17582931_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 17

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. story_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 18

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 19

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 20

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. api_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. api

        - **Similarity Score:** 0.5

      #### Item 21

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. api_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. api

        - **Similarity Score:** 0.5

      #### Item 22

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 23

        ## Documents

          ### Documents Details

          1. conf_api_17582931_1
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 24

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. conf_requirements_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 25

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. conf_security_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 26

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. conf_testing_17582931_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 27

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. conf_deployment_17582931_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 28

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. story_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 29

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 30

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 31

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 32

        ## Documents

          ### Documents Details

          1. conf_design_17582931_2
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 33

        ## Documents

          ### Documents Details

          1. conf_requirements_17582931_3
          2. conf_security_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 34

        ## Documents

          ### Documents Details

          1. conf_requirements_17582931_3
          2. conf_testing_17582931_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 35

        ## Documents

          ### Documents Details

          1. conf_requirements_17582931_3
          2. conf_deployment_17582931_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 36

        ## Documents

          ### Documents Details

          1. conf_requirements_17582931_3
          2. story_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 37

        ## Documents

          ### Documents Details

          1. conf_requirements_17582931_3
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 38

        ## Documents

          ### Documents Details

          1. conf_requirements_17582931_3
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 39

        ## Documents

          ### Documents Details

          1. conf_requirements_17582931_3
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 40

        ## Documents

          ### Documents Details

          1. conf_requirements_17582931_3
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 41

        ## Documents

          ### Documents Details

          1. conf_security_17582931_4
          2. conf_testing_17582931_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 42

        ## Documents

          ### Documents Details

          1. conf_security_17582931_4
          2. conf_deployment_17582931_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 43

        ## Documents

          ### Documents Details

          1. conf_security_17582931_4
          2. story_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 44

        ## Documents

          ### Documents Details

          1. conf_security_17582931_4
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 45

        ## Documents

          ### Documents Details

          1. conf_security_17582931_4
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 46

        ## Documents

          ### Documents Details

          1. conf_security_17582931_4
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 47

        ## Documents

          ### Documents Details

          1. conf_security_17582931_4
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 48

        ## Documents

          ### Documents Details

          1. conf_testing_17582931_5
          2. conf_deployment_17582931_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. go

        - **Similarity Score:** 0.75

      #### Item 49

        ## Documents

          ### Documents Details

          1. conf_testing_17582931_5
          2. story_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 50

        ## Documents

          ### Documents Details

          1. conf_testing_17582931_5
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 51

        ## Documents

          ### Documents Details

          1. conf_testing_17582931_5
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 52

        ## Documents

          ### Documents Details

          1. conf_testing_17582931_5
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 53

        ## Documents

          ### Documents Details

          1. conf_testing_17582931_5
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 54

        ## Documents

          ### Documents Details

          1. conf_deployment_17582931_6
          2. story_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 55

        ## Documents

          ### Documents Details

          1. conf_deployment_17582931_6
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 56

        ## Documents

          ### Documents Details

          1. conf_deployment_17582931_6
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 57

        ## Documents

          ### Documents Details

          1. conf_deployment_17582931_6
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 58

        ## Documents

          ### Documents Details

          1. conf_deployment_17582931_6
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte

        - **Similarity Score:** 0.5

      #### Item 59

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_0
          2. jira_bug_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 60

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_0
          2. jira_feature_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. high
          2. education
          3. jira
          4. feature

        - **Similarity Score:** 1

      #### Item 61

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_0
          2. jira_feature_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education
          3. feature

        - **Similarity Score:** 0.75

      #### Item 62

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_0
          2. jira_user_story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. high
          2. education
          3. jira

        - **Similarity Score:** 0.75

      #### Item 63

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_0
          2. bug_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 64

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_0
          2. bug_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 65

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_0
          2. bug_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 66

        ## Documents

          ### Documents Details

          1. jira_bug_17582931_1
          2. jira_feature_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 67

        ## Documents

          ### Documents Details

          1. jira_bug_17582931_1
          2. jira_feature_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 68

        ## Documents

          ### Documents Details

          1. jira_bug_17582931_1
          2. jira_user_story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 69

        ## Documents

          ### Documents Details

          1. jira_bug_17582931_1
          2. bug_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education
          3. bug

        - **Similarity Score:** 0.75

      #### Item 70

        ## Documents

          ### Documents Details

          1. jira_bug_17582931_1
          2. bug_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education
          3. bug

        - **Similarity Score:** 0.75

      #### Item 71

        ## Documents

          ### Documents Details

          1. jira_bug_17582931_1
          2. bug_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education
          3. bug

        - **Similarity Score:** 0.75

      #### Item 72

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_2
          2. jira_feature_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education
          3. feature

        - **Similarity Score:** 0.75

      #### Item 73

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_2
          2. jira_user_story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. high
          2. education
          3. jira

        - **Similarity Score:** 0.75

      #### Item 74

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_2
          2. bug_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 75

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_2
          2. bug_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 76

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_2
          2. bug_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 77

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_3
          2. jira_user_story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 78

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_3
          2. bug_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 79

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_3
          2. bug_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 80

        ## Documents

          ### Documents Details

          1. jira_feature_17582931_3
          2. bug_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 81

        ## Documents

          ### Documents Details

          1. jira_user_story_17582931_4
          2. story_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 82

        ## Documents

          ### Documents Details

          1. jira_user_story_17582931_4
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 83

        ## Documents

          ### Documents Details

          1. jira_user_story_17582931_4
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 84

        ## Documents

          ### Documents Details

          1. jira_user_story_17582931_4
          2. bug_17582931_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 85

        ## Documents

          ### Documents Details

          1. jira_user_story_17582931_4
          2. bug_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 86

        ## Documents

          ### Documents Details

          1. jira_user_story_17582931_4
          2. bug_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education

        - **Similarity Score:** 0.5

      #### Item 87

        ## Documents

          ### Documents Details

          1. jira_user_story_17582931_4
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 88

        ## Documents

          ### Documents Details

          1. jira_user_story_17582931_4
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 89

        ## Documents

          ### Documents Details

          1. pr_17582931_0
          2. pr_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. pr
          2. education
          3. review
          4. github

        - **Similarity Score:** 1

      #### Item 90

        ## Documents

          ### Documents Details

          1. pr_17582931_0
          2. pr_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. pr
          2. education
          3. review
          4. github

        - **Similarity Score:** 1

      #### Item 91

        ## Documents

          ### Documents Details

          1. pr_17582931_1
          2. pr_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. pr
          2. education
          3. review
          4. github

        - **Similarity Score:** 1

      #### Item 92

        ## Documents

          ### Documents Details

          1. story_17582931_0
          2. story_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 93

        ## Documents

          ### Documents Details

          1. story_17582931_0
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 94

        ## Documents

          ### Documents Details

          1. story_17582931_0
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 95

        ## Documents

          ### Documents Details

          1. story_17582931_0
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 96

        ## Documents

          ### Documents Details

          1. story_17582931_1
          2. story_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 97

        ## Documents

          ### Documents Details

          1. story_17582931_1
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 98

        ## Documents

          ### Documents Details

          1. story_17582931_1
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 99

        ## Documents

          ### Documents Details

          1. story_17582931_2
          2. story_17582931_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 100

        ## Documents

          ### Documents Details

          1. story_17582931_2
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1

      #### Item 101

        ## Documents

          ### Documents Details

          1. rfc_17582931_0
          2. rfc_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. rfc
          3. proposal

        - **Similarity Score:** 1

      #### Item 102

        ## Documents

          ### Documents Details

          1. meeting_17582931_0
          2. meeting_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. meeting
          2. education
          3. notes

        - **Similarity Score:** 1

      #### Item 103

        ## Documents

          ### Documents Details

          1. testplan_17582931_0
          2. testplan_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. plan
          2. test
          3. education

        - **Similarity Score:** 1

      #### Item 104

        ## Documents

          ### Documents Details

          1. deploy_17582931_0
          2. deploy_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. guide
          3. deploy

        - **Similarity Score:** 1

      #### Item 105

        ## Documents

          ### Documents Details

          1. bug_17582931_0
          2. bug_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education
          3. bug

        - **Similarity Score:** 1

      #### Item 106

        ## Documents

          ### Documents Details

          1. bug_17582931_0
          2. bug_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education
          3. bug

        - **Similarity Score:** 1

      #### Item 107

        ## Documents

          ### Documents Details

          1. bug_17582931_1
          2. bug_17582931_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. education
          3. bug

        - **Similarity Score:** 1

      #### Item 108

        ## Documents

          ### Documents Details

          1. api_17582931_0
          2. api_17582931_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. api
          3. rest
          4. documentation

        - **Similarity Score:** 1

      #### Item 109

        ## Documents

          ### Documents Details

          1. story_17582931_3
          2. story_17582931_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. svelte
          3. user_story

        - **Similarity Score:** 1


    ## Category Relationships

      ## Architecture

        ### Architecture Details

        1. conf_architecture_17582931_0

      ## Api

        ### Api Details

        1. conf_api_17582931_1
        2. api_17582931_0
        3. api_17582931_1

      ## Design

        ### Design Details

        1. conf_design_17582931_2

      ## Requirements

        ### Requirements Details

        1. conf_requirements_17582931_3

      ## Security

        ### Security Details

        1. conf_security_17582931_4

      ## Testing

        ### Testing Details

        1. conf_testing_17582931_5
        2. testplan_17582931_0
        3. testplan_17582931_1

      ## Deployment

        ### Deployment Details

        1. conf_deployment_17582931_6
        2. deploy_17582931_0
        3. deploy_17582931_1

      ## Feature

        ### Feature Details

        1. jira_feature_17582931_0
        2. jira_feature_17582931_2
        3. jira_feature_17582931_3

      ## Bug

        ### Bug Details

        1. jira_bug_17582931_1
        2. bug_17582931_0
        3. bug_17582931_1
        4. bug_17582931_2

      ## User Story

        ### User Story Details

        1. jira_user_story_17582931_4
        2. story_17582931_0
        3. story_17582931_1
        4. story_17582931_2
        5. story_17582931_3
        6. story_17582931_4

      ## Development

        ### Development Details

        1. pr_17582931_0
        2. pr_17582931_1
        3. pr_17582931_2

      ## Rfc

        ### Rfc Details

        1. rfc_17582931_0
        2. rfc_17582931_1

      ## Meeting Notes

        ### Meeting Notes Details

        1. meeting_17582931_0
        2. meeting_17582931_1


    ## Content Clusters

      ### Content Clusters Details




## Recommendations

  ### Recommendations Details

  #### Item 1

    - **Type:** category_balance
    - **Priority:** low
    - **Description:** Categories with only one document: architecture, design, requirements, security. Consider adding more documents to these categories.
    - **Confidence:** 0.7
    ## Unbalanced Categories

      ### Unbalanced Categories Details

      1. architecture
      2. design
      3. requirements
      4. security



- **Recommendations Count:** 1
## Timeline Analysis

  - **Total Phases:** 4
  - **Documents Per Phase:** 8
  - **Timeline Coverage:** Multi-document batch analysis
  ## Document Evolution

    ## Chronological Order

      ### Chronological Order Details

      1. rfc_17582931_1
      2. jira_bug_17582931_1
      3. jira_feature_17582931_3
      4. bug_17582931_1
      5. bug_17582931_2
      6. conf_security_17582931_4
      7. conf_requirements_17582931_3
      8. deploy_17582931_0
      9. pr_17582931_2
      10. conf_testing_17582931_5
      11. conf_design_17582931_2
      12. api_17582931_0
      13. conf_architecture_17582931_0
      14. story_17582931_4
      15. testplan_17582931_1
      16. bug_17582931_0
      17. jira_feature_17582931_2
      18. conf_deployment_17582931_6
      19. meeting_17582931_1
      20. rfc_17582931_0
      21. deploy_17582931_1
      22. meeting_17582931_0
      23. story_17582931_2
      24. jira_user_story_17582931_4
      25. story_17582931_0
      26. api_17582931_1
      27. conf_api_17582931_1
      28. testplan_17582931_0
      29. story_17582931_3
      30. story_17582931_1
      31. pr_17582931_1
      32. jira_feature_17582931_0
      33. pr_17582931_0

    ## Creation Dates

      ### Creation Dates Details

      1. 2025-08-21T14:46:23.005478
      2. 2025-08-29T18:21:23.005478
      3. 2025-08-31T02:49:23.005478
      4. 2025-09-01T22:43:23.005478
      5. 2025-09-04T10:00:23.005478
      6. 2025-09-06T08:27:23.005478
      7. 2025-09-06T09:28:23.005478
      8. 2025-09-08T15:42:23.005478
      9. 2025-09-09T02:18:23.005478
      10. 2025-09-09T07:38:23.005478
      11. 2025-09-09T19:25:23.005478
      12. 2025-09-10T01:10:23.005478
      13. 2025-09-10T05:51:23.005478
      14. 2025-09-10T09:43:23.005478
      15. 2025-09-10T14:14:23.005478
      16. 2025-09-12T04:50:23.005478
      17. 2025-09-12T13:01:23.005478
      18. 2025-09-12T20:38:23.005478
      19. 2025-09-12T23:40:23.005478
      20. 2025-09-13T11:55:23.005478
      21. 2025-09-13T17:54:23.005478
      22. 2025-09-14T02:14:23.005478
      23. 2025-09-14T12:36:23.005478
      24. 2025-09-14T15:35:23.005478
      25. 2025-09-15T05:12:23.005478
      26. 2025-09-15T20:41:23.005478
      27. 2025-09-16T11:59:23.005478
      28. 2025-09-16T18:57:23.005478
      29. 2025-09-17T07:21:23.005478
      30. 2025-09-17T21:01:23.005478
      31. 2025-09-18T11:44:23.005478
      32. 2025-09-18T12:07:23.005478
      33. 2025-09-18T13:51:23.005478

    ## Category Evolution

      ## Rfc

        ### Rfc Details

        1. rfc_17582931_1
        2. rfc_17582931_0

      ## Bug

        ### Bug Details

        1. jira_bug_17582931_1
        2. bug_17582931_1
        3. bug_17582931_2
        4. bug_17582931_0

      ## Feature

        ### Feature Details

        1. jira_feature_17582931_3
        2. jira_feature_17582931_2
        3. jira_feature_17582931_0

      ## Security

        ### Security Details

        1. conf_security_17582931_4

      ## Requirements

        ### Requirements Details

        1. conf_requirements_17582931_3

      ## Deployment

        ### Deployment Details

        1. deploy_17582931_0
        2. conf_deployment_17582931_6
        3. deploy_17582931_1

      ## Development

        ### Development Details

        1. pr_17582931_2
        2. pr_17582931_1
        3. pr_17582931_0

      ## Testing

        ### Testing Details

        1. conf_testing_17582931_5
        2. testplan_17582931_1
        3. testplan_17582931_0

      ## Design

        ### Design Details

        1. conf_design_17582931_2

      ## Api

        ### Api Details

        1. api_17582931_0
        2. api_17582931_1
        3. conf_api_17582931_1

      ## Architecture

        ### Architecture Details

        1. conf_architecture_17582931_0

      ## User Story

        ### User Story Details

        1. story_17582931_4
        2. story_17582931_2
        3. jira_user_story_17582931_4
        4. story_17582931_0
        5. story_17582931_3
        6. story_17582931_1

      ## Meeting Notes

        ### Meeting Notes Details

        1. meeting_17582931_1
        2. meeting_17582931_0




## Quality Metrics

  - **Total Documents:** 33
  - **Processed Documents:** 33
  - **Processing Success Rate:** 100
  - **Categories Covered:** 13
  - **Total Tags:** 30
  - **Average Tags Per Document:** 3.515151515151515
  - **Quality Score:** 100

## Alignment Analysis

  - **Success:** ✅ Yes
  - **Overall Alignment Score:** 85.5
  ## Alignment Issues

    ### Alignment Issues Details

    #### Item 1

      - **Type:** terminology_inconsistency
      - **Severity:** medium
      - **Description:** Found potential terminology inconsistencies
      ## Affected Documents

        ### Affected Documents Details

        1. conf_architecture_17582931_0
        2. conf_api_17582931_1

      - **Recommendation:** Review terminology usage across documents


  ## Consistency Report

    - **Format Consistency Score:** 0.8
    - **Structure Consistency Score:** 0.7

  ## Terminology Analysis

    - **Cross Document Terms:** 15
    - **Inconsistent Terms:** 3

  ## Pattern Analysis

    - **Pattern Deviations:** 2

  ## Conflict Detection

    - **Version Conflicts:** 0

  ## Recommendations

    ### Recommendations Details

    #### Item 1

      - **Type:** terminology_standardization
      - **Priority:** medium
      - **Description:** Standardize terminology across documents
      - **Confidence:** 0.8


  - **Processing Time:** 0.5

## Document Dump

  - **Success:** ✅ Yes
  - **Report Type:** document_dump
  - **Document Count:** 33
  - **Format:** markdown
  - **Content:** # Document Dump Report
Generated: 2025-09-19 09:45:23

## Summary
- Total Documents: 33
- Document Types: pr, jira, user_story, test_plan, confluence, meeting_notes, deployment_guide, rfc

## Documents by Type


### PR Documents (3)

#### 1. PR: Education - Feature #696

**ID:** pr_17582931_0
**Author:** John Doe
**Created:** 2025-09-18T13:51:23.005478
**Updated:** 2025-09-17T03:01:23.005478
**Status:** open
**Category:** development
**Tags:** pr, github, review, education

**Content:**
```
## Description
Implements bugfix for education module.

## Changes
- Updated API logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-725

```

#### 2. PR: Education - Bugfix #821

**ID:** pr_17582931_1
**Author:** Mike Chen
**Created:** 2025-09-18T11:44:23.005478
**Updated:** 2025-09-19T02:23:23.005478
**Status:** review
**Category:** development
**Tags:** pr, github, review, education

**Content:**
```
## Description
Implements feature for education module.

## Changes
- Updated database logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-678

```

#### 3. PR: Education - Feature #639

**ID:** pr_17582931_2
**Author:** Priya Patel
**Created:** 2025-09-09T02:18:23.005478
**Updated:** 2025-09-18T15:02:23.005478
**Status:** review
**Category:** development
**Tags:** pr, github, review, education

**Content:**
```
## Description
Implements refactor for education module.

## Changes
- Updated authentication logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-552

```


### JIRA Documents (8)

#### 1. Implement Advanced Education Dashboard

**ID:** jira_feature_17582931_0
**Author:** Alex Thompson
**Created:** 2025-09-18T12:07:23.005478
**Updated:** 2025-09-19T06:33:23.005478
**Status:** in_progress
**Category:** feature
**Tags:** feature, high, jira, education
**Assignee:** Emma Wilson
**Priority:** high

**Content:**
```
As a product manager, I want an advanced dashboard so I can track education platform metrics.

## Acceptance Criteria
- Real-time metrics
- Svelte frontend
- Go backend API
- Mobile-responsive
```

#### 2. Story: As a user, I can reset my password via email

**ID:** jira_user_story_17582931_4
**Author:** Alex Thompson
**Created:** 2025-09-14T15:35:23.005478
**Updated:** 2025-09-15T04:21:23.005478
**Status:** resolved
**Category:** user_story
**Tags:** user_story, high, jira, education
**Assignee:** Priya Patel
**Priority:** high

**Content:**
```
User should be able to request password reset and receive a secure email link.

## Acceptance Criteria
- Email sent to user
- Link expires in 30 minutes
- Password complexity enforced
```

#### 3. Epic: Education Mobile App Launch

**ID:** jira_feature_17582931_2
**Author:** David Kim
**Created:** 2025-09-12T13:01:23.005478
**Updated:** 2025-09-16T11:50:23.005478
**Status:** open
**Category:** feature
**Tags:** feature, high, jira, education
**Assignee:** Emma Wilson
**Priority:** high

**Content:**
```
Epic to track all work for mobile app launch.

## Child Issues
- JIRA-123: Mobile UI
- JIRA-124: API integration
- JIRA-125: Push notifications
```

#### 4. Bug: Education - UI crash

**ID:** bug_17582931_0
**Author:** John Doe
**Created:** 2025-09-12T04:50:23.005478
**Updated:** 2025-09-14T08:43:23.005478
**Status:** in_progress
**Category:** bug
**Tags:** bug, jira, education
**Assignee:** Emma Wilson
**Priority:** high

**Content:**
```
Steps to Reproduce:
1. Navigate to dashboard
2. Observe error

## Expected
Graceful error message

## Actual
UI freezes

## Logs
```
[stacktrace]
```

```

#### 5. Bug: Education - Timeout error

**ID:** bug_17582931_2
**Author:** Alex Thompson
**Created:** 2025-09-04T10:00:23.005478
**Updated:** 2025-09-19T01:49:23.005478
**Status:** resolved
**Category:** bug
**Tags:** bug, jira, education
**Assignee:** Sarah Johnson
**Priority:** high

**Content:**
```
Steps to Reproduce:
1. Navigate to dashboard
2. Observe error

## Expected
Graceful error message

## Actual
500 Internal Server Error

## Logs
```
[stacktrace]
```

```

#### 6. Bug: Education - UI crash

**ID:** bug_17582931_1
**Author:** David Kim
**Created:** 2025-09-01T22:43:23.005478
**Updated:** 2025-09-16T12:34:23.005478
**Status:** open
**Category:** bug
**Tags:** bug, jira, education
**Assignee:** Sarah Johnson
**Priority:** high

**Content:**
```
Steps to Reproduce:
1. Login with invalid credentials
2. Observe error

## Expected
Graceful error message

## Actual
500 Internal Server Error

## Logs
```
[stacktrace]
```

```

#### 7. Task: Refactor Go Service Layer

**ID:** jira_feature_17582931_3
**Author:** Mike Chen
**Created:** 2025-08-31T02:49:23.005478
**Updated:** 2025-09-19T06:40:23.005478
**Status:** review
**Category:** feature
**Tags:** feature, medium, jira, education
**Assignee:** Sarah Johnson
**Priority:** medium

**Content:**
```
Refactor service layer for maintainability and testability.

## Subtasks
- Add unit tests
- Extract business logic
- Update documentation
```

#### 8. Bug: Education API returns 500 on POST /items

**ID:** jira_bug_17582931_1
**Author:** John Doe
**Created:** 2025-08-29T18:21:23.005478
**Updated:** 2025-09-16T05:05:23.005478
**Status:** open
**Category:** bug
**Tags:** bug, critical, jira, education
**Assignee:** Priya Patel
**Priority:** critical

**Content:**
```
Steps to Reproduce:
1. POST to /api/v1/education/items with invalid payload
2. Observe 500 error

## Expected
Graceful validation error (400)

## Actual
500 Internal Server Error

## Logs
```
[stacktrace]
```
```


### USER_STORY Documents (5)

#### 1. User Story: As an admin...

**ID:** story_17582931_1
**Author:** Sarah Johnson
**Created:** 2025-09-17T21:01:23.005478
**Updated:** 2025-09-19T00:23:23.005478
**Status:** review
**Category:** user_story
**Tags:** user_story, education, svelte

**Content:**
```
As a admin, I want to export data so that I can get timely alerts.

## Acceptance Criteria
- Email notifications
- Audit logs

```

#### 2. User Story: As a user, I can change settings

**ID:** story_17582931_3
**Author:** Priya Patel
**Created:** 2025-09-17T07:21:23.005478
**Updated:** 2025-09-19T05:35:23.005478
**Status:** open
**Category:** user_story
**Tags:** user_story, education, svelte

**Content:**
```
As a user, I want to change settings so that I can customize experience.

## Acceptance Criteria
- Email alerts
- Auditable

```

#### 3. User Story: As a user...

**ID:** story_17582931_0
**Author:** Alex Thompson
**Created:** 2025-09-15T05:12:23.005478
**Updated:** 2025-09-19T08:15:23.005478
**Status:** in_progress
**Category:** user_story
**Tags:** user_story, education, svelte

**Content:**
```
As a developer, I want to reset password so that I can get timely alerts.

## Acceptance Criteria
- Secure reset
- Mobile support

```

#### 4. User Story: As a user...

**ID:** story_17582931_2
**Author:** David Kim
**Created:** 2025-09-14T12:36:23.005478
**Updated:** 2025-09-18T13:54:23.005478
**Status:** published
**Category:** user_story
**Tags:** user_story, education, svelte

**Content:**
```
As a user, I want to customize dashboard so that I can get timely alerts.

## Acceptance Criteria
- Export as CSV
- Audit logs

```

#### 5. User Story: As a user, I can receive alerts

**ID:** story_17582931_4
**Author:** John Doe
**Created:** 2025-09-10T09:43:23.005478
**Updated:** 2025-09-18T21:14:23.005478
**Status:** resolved
**Category:** user_story
**Tags:** user_story, education, svelte

**Content:**
```
As a user, I want to change settings so that I can customize experience.

## Acceptance Criteria
- Email alerts
- Accessible

```


### TEST_PLAN Documents (2)

#### 1. Test Plan: Education Authentication

**ID:** testplan_17582931_0
**Author:** Priya Patel
**Created:** 2025-09-16T18:57:23.005478
**Updated:** 2025-09-17T07:29:23.005478
**Status:** published
**Category:** testing
**Tags:** test, plan, education

**Content:**
```
# Test Plan

## Scope
- API module

## Objectives
- Validate access control

## Test Cases
- Login with valid/invalid credentials
- Error messages

## Tooling
- Pytest

## Exit Criteria
- 100% test pass

```

#### 2. Test Plan: Education UI

**ID:** testplan_17582931_1
**Author:** Mike Chen
**Created:** 2025-09-10T14:14:23.005478
**Updated:** 2025-09-17T10:10:23.005478
**Status:** published
**Category:** testing
**Tags:** test, plan, education

**Content:**
```
# Test Plan

## Scope
- UI module

## Objectives
- Validate login

## Test Cases
- API returns correct status codes
- Session timeout

## Tooling
- Cypress

## Exit Criteria
- 100% test pass

```


### CONFLUENCE Documents (9)

#### 1. API Documentation - Education Service

**ID:** conf_api_17582931_1
**Author:** Jane Smith
**Created:** 2025-09-16T11:59:23.005478
**Updated:** 2025-09-17T12:46:23.005478
**Status:** published
**Category:** api
**Tags:** api, education, svelte, go

**Content:**
```
# Education Service API

## Overview
RESTful and GraphQL APIs for education platform operations.

## Authentication
All API requests require JWT token authentication and API key header.

## Endpoints
### GET /api/v1/education/items
Retrieves a list of education items.

**Response:**
```json
{
  "items": [
    {
      "id": "123",
      "name": "Sample Item",
      "status": "active"
    }
  ]
}
```

### POST /api/v1/education/items
Creates a new item.

**Request Body:**
```json
{
  "name": "New Item",
  "description": "Detailed description."
}
```

```

#### 2. API Documentation - Education Endpoint 3

**ID:** api_17582931_1
**Author:** Priya Patel
**Created:** 2025-09-15T20:41:23.005478
**Updated:** 2025-09-17T18:33:23.005478
**Status:** published
**Category:** api
**Tags:** api, documentation, rest, education

**Content:**
```
# API Endpoint 3

## Method
DELETE /api/v1/education/endpoint3

## Description
Updates an entity.

## Request/Response
```json
{ "id": "abc1", "result": "ok" }
```

```

#### 3. Deployment Guide - Education Platform

**ID:** conf_deployment_17582931_6
**Author:** John Doe
**Created:** 2025-09-12T20:38:23.005478
**Updated:** 2025-09-19T02:12:23.005478
**Status:** published
**Category:** deployment
**Tags:** deployment, education, svelte, go

**Content:**
```
# Deployment Guide

## Environments
- Dev, Staging, Prod

## CI/CD
- GitHub Actions, ArgoCD, DockerHub

## Rollback
- Blue/green, canary
- Rollback steps

```

#### 4. Education Platform - System Architecture

**ID:** conf_architecture_17582931_0
**Author:** Jane Smith
**Created:** 2025-09-10T05:51:23.005478
**Updated:** 2025-09-17T22:58:23.005478
**Status:** published
**Category:** architecture
**Tags:** architecture, education, svelte, go

**Content:**
```
# Education Platform Architecture

## Overview
The education platform is built on microservices architecture for scalability and resilience.

## Core Components
- **User Management Service**: Handles authentication, SSO, and user profiles
- **Business Logic Engine**: Implements core education domain logic with robust validation
- **Data Processing Service**: Real-time analytics, ETL pipelines, and reporting
- **Notification Service**: Asynchronous event-driven notifications (email, SMS, webhooks)

## Technology Stack
- Frontend: Svelte (SPA, SSR, PWA support)
- Backend: Go (REST & GraphQL APIs)
- Database: PostgreSQL, Redis, S3
- Infrastructure: Docker, Kubernetes, Terraform, CI/CD

## Security
- OAuth2, RBAC, audit logging, encrypted secrets

## Scalability
- Horizontal scaling, autoscaling, load balancing

## Diagram
```
[Insert architecture diagram here]
```

```

#### 5. API Documentation - Education Endpoint 2

**ID:** api_17582931_0
**Author:** Priya Patel
**Created:** 2025-09-10T01:10:23.005478
**Updated:** 2025-09-18T05:02:23.005478
**Status:** published
**Category:** api
**Tags:** api, documentation, rest, education

**Content:**
```
# API Endpoint 2

## Method
DELETE /api/v1/education/endpoint2

## Description
Retrieves an entity.

## Request/Response
```json
{ "id": "abc0", "result": "ok" }
```

```

#### 6. Design Document - Education Notifications

**ID:** conf_design_17582931_2
**Author:** John Doe
**Created:** 2025-09-09T19:25:23.005478
**Updated:** 2025-09-17T23:33:23.005478
**Status:** published
**Category:** design
**Tags:** design, education, svelte, go

**Content:**
```
# Design Doc: Notification Service

## Purpose
Design for asynchronous, scalable notification delivery supporting email, SMS, and push.

## Requirements
- Pluggable provider architecture
- Guaranteed delivery and retry
- Idempotency
- Auditable logs

## Sequence Diagram
```
[Insert sequence diagram]
```

## Open Questions
- How to handle provider outages?
- SLA for delivery latency?

```

#### 7. Testing Strategy - Education Platform

**ID:** conf_testing_17582931_5
**Author:** David Kim
**Created:** 2025-09-09T07:38:23.005478
**Updated:** 2025-09-16T16:25:23.005478
**Status:** published
**Category:** testing
**Tags:** testing, education, svelte, go

**Content:**
```
# Testing Strategy

## Types
- Unit, integration, E2E, load, security

## Tooling
- Pytest, Cypress, Postman, Snyk

## Coverage
- 90%+ unit test coverage
- Automated regression suite

```

#### 8. Requirements Specification - Education Onboarding

**ID:** conf_requirements_17582931_3
**Author:** Emma Wilson
**Created:** 2025-09-06T09:28:23.005478
**Updated:** 2025-09-18T21:09:23.005478
**Status:** published
**Category:** requirements
**Tags:** requirements, education, svelte, go

**Content:**
```
# Requirements: User Onboarding

## Functional
- Collect user info (name, email, org)
- Email verification
- Welcome tour

## Non-Functional
- Onboarding completion < 2 minutes
- Accessible (WCAG 2.1 AA)
- GDPR compliant

```

#### 9. Security Overview - Education Platform

**ID:** conf_security_17582931_4
**Author:** Lisa Rodriguez
**Created:** 2025-09-06T08:27:23.005478
**Updated:** 2025-09-19T02:16:23.005478
**Status:** published
**Category:** security
**Tags:** security, education, svelte, go

**Content:**
```
# Security Overview

## Threat Model
- External attackers
- Insider threats
- Data exfiltration

## Controls
- Encryption at rest/in transit
- RBAC, MFA, audit logs
- Regular penetration testing

## Incident Response
- 24/7 monitoring
- Runbooks

```


### MEETING_NOTES Documents (2)

#### 1. Meeting Notes: Sprint Planning

**ID:** meeting_17582931_0
**Author:** Emma Wilson
**Created:** 2025-09-14T02:14:23.005478
**Updated:** 2025-09-19T00:04:23.005478
**Status:** published
**Category:** meeting_notes
**Tags:** meeting, notes, education

**Content:**
```
# Meeting Notes

**Date:** 2025-09-10T13:05:23.005478
**Attendees:** Sarah Johnson, Lisa Rodriguez, Priya Patel, Alex Thompson

## Agenda
- Review sprint goals
- Q&A

## Notes
- Identified key technical debt
- Schedule security review

## Action Items
- Prepare demo

```

#### 2. Meeting Notes: Sprint Planning

**ID:** meeting_17582931_1
**Author:** David Kim
**Created:** 2025-09-12T23:40:23.005478
**Updated:** 2025-09-19T08:37:23.005478
**Status:** published
**Category:** meeting_notes
**Tags:** meeting, notes, education

**Content:**
```
# Meeting Notes

**Date:** 2025-09-11T08:22:23.005478
**Attendees:** Lisa Rodriguez, John Doe, David Kim, Alex Thompson

## Agenda
- Review sprint goals
- Architecture discussion

## Notes
- Identified key technical debt
- Follow up with DevOps

## Action Items
- Fix critical bug

```


### DEPLOYMENT_GUIDE Documents (2)

#### 1. Deployment Guide: Education Dev

**ID:** deploy_17582931_1
**Author:** Mike Chen
**Created:** 2025-09-13T17:54:23.005478
**Updated:** 2025-09-18T13:18:23.005478
**Status:** published
**Category:** deployment
**Tags:** deploy, guide, education

**Content:**
```
# Deployment Guide

## Environment
- Production

## Steps
- Build Docker image
- Push to registry
- Deploy with ArgoCD
- Run smoke tests

## Rollback
- Rollback to previous release
- Notify stakeholders

```

#### 2. Deployment Guide: Education Dev

**ID:** deploy_17582931_0
**Author:** Mike Chen
**Created:** 2025-09-08T15:42:23.005478
**Updated:** 2025-09-18T18:38:23.005478
**Status:** published
**Category:** deployment
**Tags:** deploy, guide, education

**Content:**
```
# Deployment Guide

## Environment
- Staging

## Steps
- Build Docker image
- Push to registry
- Deploy with ArgoCD
- Run smoke tests

## Rollback
- Rollback to previous release
- Notify stakeholders

```


### RFC Documents (2)

#### 1. RFC: Migrate to Kubernetes

**ID:** rfc_17582931_0
**Author:** David Kim
**Created:** 2025-09-13T11:55:23.005478
**Updated:** 2025-09-18T05:23:23.005478
**Status:** open
**Category:** rfc
**Tags:** rfc, proposal, education

**Content:**
```
# RFC: Migrate to Kubernetes

## Motivation
Enhance scalability

## Proposal
- Migrate deployment to Kubernetes
- Update documentation
- Provide migration plan

## Drawbacks
- Learning curve

## Alternatives
- Keep current approach
- Evaluate other tools

```

#### 2. RFC: Switch to GraphQL

**ID:** rfc_17582931_1
**Author:** Mike Chen
**Created:** 2025-08-21T14:46:23.005478
**Updated:** 2025-09-17T03:51:23.005478
**Status:** open
**Category:** rfc
**Tags:** rfc, proposal, education

**Content:**
```
# RFC: Migrate to Kubernetes

## Motivation
Standardize API schema

## Proposal
- Switch REST to GraphQL
- Update documentation
- Provide migration plan

## Drawbacks
- Compatibility issues

## Alternatives
- Keep current approach
- Evaluate other tools

```


  ## Metadata

    - **Generated At:** 2025-09-19T09:45:23.349096
    - **Total Documents:** 33
    ## Document Types

      ### Document Types Details

      1. pr
      2. jira
      3. user_story
      4. test_plan
      5. confluence
      6. meeting_notes
      7. deployment_guide
      8. rfc

    - **Sorted By:** dateCreated
    - **Sort Order:** desc



