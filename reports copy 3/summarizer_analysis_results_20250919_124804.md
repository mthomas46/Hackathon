# 📊 Comprehensive Analysis Results Report

**Report Generated:** 2025-09-19 12:48:04 UTC
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

    - **Document Id:** conf_architecture_17583040_0
    - **Title:** E-Commerce Platform - System Architecture
    - **Category:** architecture
    ## Tags

      ### Tags Details

      1. architecture
      2. e-commerce
      3. next.js
      4. rust

    - **Summary:** # E-Commerce Platform Architecture

## Overview
The e-commerce platform is built on microservices architecture for scalability and resilience.

## Core Components
- **User Management Service**: Handles authentication, SSO, and user profiles
- **Business Logic Engine**: Implements core e-commerce domain logic with robust validation
- **Data Processing Service**: Real-time analytics, ETL pipelines, and reporting
- **Notification Service**: Asynchronous event-driven notifications (email, SMS, webhooks)

## Technology Stack
- Frontend: Next.js (SPA, SSR, PWA support)
- Backend: Rust (REST & GraphQL APIs)
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

    - **Document Id:** conf_api_17583040_1
    - **Title:** API Documentation - E-Commerce Service
    - **Category:** api
    ## Tags

      ### Tags Details

      1. api
      2. e-commerce
      3. next.js
      4. rust

    - **Summary:** # E-Commerce Service API

## Overview
RESTful and GraphQL APIs for e-commerce platform operations.

## Authentication
All API requests require JWT token authentication and API key header.

## Endpoints
### GET /api/v1/e_commerce/items
Retrieves a list of e-commerce items.

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

### POST /api/v1/e_commerce/items
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

    - **Document Id:** conf_design_17583040_2
    - **Title:** Design Document - E-Commerce Notifications
    - **Category:** design
    ## Tags

      ### Tags Details

      1. design
      2. e-commerce
      3. next.js
      4. rust

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

    - **Document Id:** conf_requirements_17583040_3
    - **Title:** Requirements Specification - E-Commerce Onboarding
    - **Category:** requirements
    ## Tags

      ### Tags Details

      1. requirements
      2. e-commerce
      3. next.js
      4. rust

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

    - **Document Id:** conf_security_17583040_4
    - **Title:** Security Overview - E-Commerce Platform
    - **Category:** security
    ## Tags

      ### Tags Details

      1. security
      2. e-commerce
      3. next.js
      4. rust

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

    - **Document Id:** conf_testing_17583040_5
    - **Title:** Testing Strategy - E-Commerce Platform
    - **Category:** testing
    ## Tags

      ### Tags Details

      1. testing
      2. e-commerce
      3. next.js
      4. rust

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

    - **Document Id:** conf_deployment_17583040_6
    - **Title:** Deployment Guide - E-Commerce Platform
    - **Category:** deployment
    ## Tags

      ### Tags Details

      1. deployment
      2. e-commerce
      3. next.js
      4. rust

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

    - **Document Id:** jira_feature_17583040_0
    - **Title:** Implement Advanced E-Commerce Dashboard
    - **Category:** feature
    ## Tags

      ### Tags Details

      1. feature
      2. high
      3. jira
      4. e-commerce

    - **Summary:** As a product manager, I want an advanced dashboard so I can track e-commerce platform metrics.

## Acceptance Criteria
- Real-time metrics
- Next.js frontend
- Rust backend API
- Mobile-responsive
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 9

    - **Document Id:** jira_bug_17583040_1
    - **Title:** Bug: E-Commerce API returns 500 on POST /items
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. critical
      3. jira
      4. e-commerce

    - **Summary:** Steps to Reproduce:
1. POST to /api/v1/e-commerce/items with invalid payload
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

    - **Document Id:** jira_feature_17583040_2
    - **Title:** Epic: E-Commerce Mobile App Launch
    - **Category:** feature
    ## Tags

      ### Tags Details

      1. feature
      2. high
      3. jira
      4. e-commerce

    - **Summary:** Epic to track all work for mobile app launch.

## Child Issues
- JIRA-123: Mobile UI
- JIRA-124: API integration
- JIRA-125: Push notifications
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 11

    - **Document Id:** jira_feature_17583040_3
    - **Title:** Task: Refactor Rust Service Layer
    - **Category:** feature
    ## Tags

      ### Tags Details

      1. feature
      2. medium
      3. jira
      4. e-commerce

    - **Summary:** Refactor service layer for maintainability and testability.

## Subtasks
- Add unit tests
- Extract business logic
- Update documentation
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 12

    - **Document Id:** jira_user_story_17583040_4
    - **Title:** Story: As a user, I can reset my password via email
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. high
      3. jira
      4. e-commerce

    - **Summary:** User should be able to request password reset and receive a secure email link.

## Acceptance Criteria
- Email sent to user
- Link expires in 30 minutes
- Password complexity enforced
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 13

    - **Document Id:** pr_17583040_0
    - **Title:** PR: E-Commerce - Bugfix #489
    - **Category:** development
    ## Tags

      ### Tags Details

      1. pr
      2. github
      3. review
      4. e-commerce

    - **Summary:** ## Description
Implements bugfix for e-commerce module.

## Changes
- Updated authentication logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-911

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 14

    - **Document Id:** pr_17583040_1
    - **Title:** PR: E-Commerce - Bugfix #511
    - **Category:** development
    ## Tags

      ### Tags Details

      1. pr
      2. github
      3. review
      4. e-commerce

    - **Summary:** ## Description
Implements bugfix for e-commerce module.

## Changes
- Updated authentication logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-262

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 15

    - **Document Id:** pr_17583040_2
    - **Title:** PR: E-Commerce - Feature #426
    - **Category:** development
    ## Tags

      ### Tags Details

      1. pr
      2. github
      3. review
      4. e-commerce

    - **Summary:** ## Description
Implements bugfix for e-commerce module.

## Changes
- Updated UI logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-280

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 16

    - **Document Id:** story_17583040_0
    - **Title:** User Story: As a developer...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. e-commerce
      3. next.js

    - **Summary:** As a developer, I want to reset password so that I can get timely alerts.

## Acceptance Criteria
- Custom widgets
- Audit logs

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 17

    - **Document Id:** story_17583040_1
    - **Title:** User Story: As an admin...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. e-commerce
      3. next.js

    - **Summary:** As a admin, I want to export data so that I can increase security.

## Acceptance Criteria
- Email notifications
- Accessible UI

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 18

    - **Document Id:** story_17583040_2
    - **Title:** User Story: As a user...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. e-commerce
      3. next.js

    - **Summary:** As a developer, I want to export data so that I can increase security.

## Acceptance Criteria
- Email notifications
- Audit logs

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 19

    - **Document Id:** rfc_17583040_0
    - **Title:** RFC: Migrate to Kubernetes
    - **Category:** rfc
    ## Tags

      ### Tags Details

      1. rfc
      2. proposal
      3. e-commerce

    - **Summary:** # RFC: Adopt OpenAPI

## Motivation
Standardize API schema

## Proposal
- Migrate deployment to Kubernetes
- Update documentation
- Provide migration plan

## Drawbacks
- Migration effort

## Alternatives
- Keep current approach
- Evaluate other tools

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 20

    - **Document Id:** rfc_17583040_1
    - **Title:** RFC: Migrate to Kubernetes
    - **Category:** rfc
    ## Tags

      ### Tags Details

      1. rfc
      2. proposal
      3. e-commerce

    - **Summary:** # RFC: Adopt OpenAPI

## Motivation
Standardize API schema

## Proposal
- Adopt OpenAPI 3.0
- Update documentation
- Provide migration plan

## Drawbacks
- Migration effort

## Alternatives
- Keep current approach
- Evaluate other tools

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 21

    - **Document Id:** meeting_17583040_0
    - **Title:** Meeting Notes: Sprint Planning
    - **Category:** meeting_notes
    ## Tags

      ### Tags Details

      1. meeting
      2. notes
      3. e-commerce

    - **Summary:** # Meeting Notes

**Date:** 2025-09-15T06:26:03.803221
**Attendees:** John Doe, David Kim, Priya Patel, Mike Chen

## Agenda
- Demo new features
- Q&A

## Notes
- Action items assigned
- Follow up with DevOps

## Action Items
- Fix critical bug

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 22

    - **Document Id:** meeting_17583040_1
    - **Title:** Meeting Notes: Design Review
    - **Category:** meeting_notes
    ## Tags

      ### Tags Details

      1. meeting
      2. notes
      3. e-commerce

    - **Summary:** # Meeting Notes

**Date:** 2025-09-17T17:50:03.803221
**Attendees:** Jane Smith, Emma Wilson, Lisa Rodriguez, Sarah Johnson

## Agenda
- Review sprint goals
- Architecture discussion

## Notes
- Identified key technical debt
- Follow up with DevOps

## Action Items
- Prepare demo

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 23

    - **Document Id:** testplan_17583040_0
    - **Title:** Test Plan: E-Commerce Authentication
    - **Category:** testing
    ## Tags

      ### Tags Details

      1. test
      2. plan
      3. e-commerce

    - **Summary:** # Test Plan

## Scope
- Authentication module

## Objectives
- Validate access control

## Test Cases
- UI is accessible
- Session timeout

## Tooling
- Postman

## Exit Criteria
- 100% test pass

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 24

    - **Document Id:** testplan_17583040_1
    - **Title:** Test Plan: E-Commerce Authentication
    - **Category:** testing
    ## Tags

      ### Tags Details

      1. test
      2. plan
      3. e-commerce

    - **Summary:** # Test Plan

## Scope
- UI module

## Objectives
- Validate input validation

## Test Cases
- Login with valid/invalid credentials
- Error messages

## Tooling
- Postman

## Exit Criteria
- 100% test pass

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 25

    - **Document Id:** deploy_17583040_0
    - **Title:** Deployment Guide: E-Commerce Production
    - **Category:** deployment
    ## Tags

      ### Tags Details

      1. deploy
      2. guide
      3. e-commerce

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

  #### Item 26

    - **Document Id:** deploy_17583040_1
    - **Title:** Deployment Guide: E-Commerce Staging
    - **Category:** deployment
    ## Tags

      ### Tags Details

      1. deploy
      2. guide
      3. e-commerce

    - **Summary:** # Deployment Guide

## Environment
- Dev

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

    - **Document Id:** bug_17583040_0
    - **Title:** Bug: E-Commerce - Login failure
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. jira
      3. e-commerce

    - **Summary:** Steps to Reproduce:
1. Submit large file
2. Observe error

## Expected
Timeout handled

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

    - **Document Id:** bug_17583040_1
    - **Title:** Bug: E-Commerce - Login failure
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. jira
      3. e-commerce

    - **Summary:** Steps to Reproduce:
1. Login with invalid credentials
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

  #### Item 29

    - **Document Id:** bug_17583040_2
    - **Title:** Bug: E-Commerce - Timeout error
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. jira
      3. e-commerce

    - **Summary:** Steps to Reproduce:
1. Submit large file
2. Observe error

## Expected
No crash

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

    - **Document Id:** api_17583040_0
    - **Title:** API Documentation - E-Commerce Endpoint 2
    - **Category:** api
    ## Tags

      ### Tags Details

      1. api
      2. documentation
      3. rest
      4. e-commerce

    - **Summary:** # API Endpoint 2

## Method
POST /api/v1/e-commerce/endpoint2

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

    - **Document Id:** api_17583040_1
    - **Title:** API Documentation - E-Commerce Endpoint 3
    - **Category:** api
    ## Tags

      ### Tags Details

      1. api
      2. documentation
      3. rest
      4. e-commerce

    - **Summary:** # API Endpoint 3

## Method
POST /api/v1/e-commerce/endpoint3

## Description
Retrieves an entity.

## Request/Response
```json
{ "id": "abc1", "result": "ok" }
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 32

    - **Document Id:** story_17583040_3
    - **Title:** User Story: As a user, I can receive alerts
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. e-commerce
      3. next.js

    - **Summary:** As a user, I want to filter data so that I can customize experience.

## Acceptance Criteria
- Filter by date
- Accessible

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 33

    - **Document Id:** story_17583040_4
    - **Title:** User Story: As a user, I can receive alerts
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. e-commerce
      3. next.js

    - **Summary:** As a user, I want to receive alerts so that I can customize experience.

## Acceptance Criteria
- Filter by date
- Accessible

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0


## Multi Document Analysis

  ## Categories Found

    ### Categories Found Details

    1. architecture
    2. testing
    3. bug
    4. deployment
    5. security
    6. api
    7. design
    8. meeting_notes
    9. feature
    10. user_story
    11. rfc
    12. requirements
    13. development

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
      - **E-Commerce:** 33
      - **Next.Js:** 12
      - **Rust:** 7
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

          1. conf_architecture_17583040_0
          2. conf_api_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 2

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. conf_design_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 3

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. conf_requirements_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 4

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. conf_security_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 5

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. conf_testing_17583040_5

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 6

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. conf_deployment_17583040_6

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 7

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. story_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 8

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 9

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 10

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 11

        ## Documents

          ### Documents Details

          1. conf_architecture_17583040_0
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 12

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. conf_design_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 13

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. conf_requirements_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 14

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. conf_security_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 15

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. conf_testing_17583040_5

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 16

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. conf_deployment_17583040_6

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 17

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. story_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 18

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 19

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 20

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. api_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. api
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 21

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. api_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. api
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 22

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 23

        ## Documents

          ### Documents Details

          1. conf_api_17583040_1
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 24

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. conf_requirements_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 25

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. conf_security_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 26

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. conf_testing_17583040_5

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 27

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. conf_deployment_17583040_6

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 28

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. story_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 29

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 30

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 31

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 32

        ## Documents

          ### Documents Details

          1. conf_design_17583040_2
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 33

        ## Documents

          ### Documents Details

          1. conf_requirements_17583040_3
          2. conf_security_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 34

        ## Documents

          ### Documents Details

          1. conf_requirements_17583040_3
          2. conf_testing_17583040_5

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 35

        ## Documents

          ### Documents Details

          1. conf_requirements_17583040_3
          2. conf_deployment_17583040_6

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 36

        ## Documents

          ### Documents Details

          1. conf_requirements_17583040_3
          2. story_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 37

        ## Documents

          ### Documents Details

          1. conf_requirements_17583040_3
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 38

        ## Documents

          ### Documents Details

          1. conf_requirements_17583040_3
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 39

        ## Documents

          ### Documents Details

          1. conf_requirements_17583040_3
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 40

        ## Documents

          ### Documents Details

          1. conf_requirements_17583040_3
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 41

        ## Documents

          ### Documents Details

          1. conf_security_17583040_4
          2. conf_testing_17583040_5

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 42

        ## Documents

          ### Documents Details

          1. conf_security_17583040_4
          2. conf_deployment_17583040_6

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 43

        ## Documents

          ### Documents Details

          1. conf_security_17583040_4
          2. story_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 44

        ## Documents

          ### Documents Details

          1. conf_security_17583040_4
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 45

        ## Documents

          ### Documents Details

          1. conf_security_17583040_4
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 46

        ## Documents

          ### Documents Details

          1. conf_security_17583040_4
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 47

        ## Documents

          ### Documents Details

          1. conf_security_17583040_4
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 48

        ## Documents

          ### Documents Details

          1. conf_testing_17583040_5
          2. conf_deployment_17583040_6

        ## Shared Tags

          ### Shared Tags Details

          1. rust
          2. e-commerce
          3. next.js

        - **Similarity Score:** 0.75

      #### Item 49

        ## Documents

          ### Documents Details

          1. conf_testing_17583040_5
          2. story_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 50

        ## Documents

          ### Documents Details

          1. conf_testing_17583040_5
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 51

        ## Documents

          ### Documents Details

          1. conf_testing_17583040_5
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 52

        ## Documents

          ### Documents Details

          1. conf_testing_17583040_5
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 53

        ## Documents

          ### Documents Details

          1. conf_testing_17583040_5
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 54

        ## Documents

          ### Documents Details

          1. conf_deployment_17583040_6
          2. story_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 55

        ## Documents

          ### Documents Details

          1. conf_deployment_17583040_6
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 56

        ## Documents

          ### Documents Details

          1. conf_deployment_17583040_6
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 57

        ## Documents

          ### Documents Details

          1. conf_deployment_17583040_6
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 58

        ## Documents

          ### Documents Details

          1. conf_deployment_17583040_6
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. e-commerce
          2. next.js

        - **Similarity Score:** 0.5

      #### Item 59

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_0
          2. jira_bug_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 60

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_0
          2. jira_feature_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. feature
          2. high
          3. jira
          4. e-commerce

        - **Similarity Score:** 1

      #### Item 61

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_0
          2. jira_feature_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. feature
          2. jira
          3. e-commerce

        - **Similarity Score:** 0.75

      #### Item 62

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_0
          2. jira_user_story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. high
          3. e-commerce

        - **Similarity Score:** 0.75

      #### Item 63

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_0
          2. bug_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 64

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_0
          2. bug_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 65

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_0
          2. bug_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 66

        ## Documents

          ### Documents Details

          1. jira_bug_17583040_1
          2. jira_feature_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 67

        ## Documents

          ### Documents Details

          1. jira_bug_17583040_1
          2. jira_feature_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 68

        ## Documents

          ### Documents Details

          1. jira_bug_17583040_1
          2. jira_user_story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 69

        ## Documents

          ### Documents Details

          1. jira_bug_17583040_1
          2. bug_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. bug
          2. jira
          3. e-commerce

        - **Similarity Score:** 0.75

      #### Item 70

        ## Documents

          ### Documents Details

          1. jira_bug_17583040_1
          2. bug_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. bug
          2. jira
          3. e-commerce

        - **Similarity Score:** 0.75

      #### Item 71

        ## Documents

          ### Documents Details

          1. jira_bug_17583040_1
          2. bug_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. bug
          2. jira
          3. e-commerce

        - **Similarity Score:** 0.75

      #### Item 72

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_2
          2. jira_feature_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. feature
          2. jira
          3. e-commerce

        - **Similarity Score:** 0.75

      #### Item 73

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_2
          2. jira_user_story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. high
          3. e-commerce

        - **Similarity Score:** 0.75

      #### Item 74

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_2
          2. bug_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 75

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_2
          2. bug_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 76

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_2
          2. bug_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 77

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_3
          2. jira_user_story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 78

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_3
          2. bug_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 79

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_3
          2. bug_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 80

        ## Documents

          ### Documents Details

          1. jira_feature_17583040_3
          2. bug_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 81

        ## Documents

          ### Documents Details

          1. jira_user_story_17583040_4
          2. story_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 82

        ## Documents

          ### Documents Details

          1. jira_user_story_17583040_4
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 83

        ## Documents

          ### Documents Details

          1. jira_user_story_17583040_4
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 84

        ## Documents

          ### Documents Details

          1. jira_user_story_17583040_4
          2. bug_17583040_0

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 85

        ## Documents

          ### Documents Details

          1. jira_user_story_17583040_4
          2. bug_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 86

        ## Documents

          ### Documents Details

          1. jira_user_story_17583040_4
          2. bug_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. jira
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 87

        ## Documents

          ### Documents Details

          1. jira_user_story_17583040_4
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 88

        ## Documents

          ### Documents Details

          1. jira_user_story_17583040_4
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce

        - **Similarity Score:** 0.5

      #### Item 89

        ## Documents

          ### Documents Details

          1. pr_17583040_0
          2. pr_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. review
          2. github
          3. e-commerce
          4. pr

        - **Similarity Score:** 1

      #### Item 90

        ## Documents

          ### Documents Details

          1. pr_17583040_0
          2. pr_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. review
          2. github
          3. e-commerce
          4. pr

        - **Similarity Score:** 1

      #### Item 91

        ## Documents

          ### Documents Details

          1. pr_17583040_1
          2. pr_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. review
          2. github
          3. e-commerce
          4. pr

        - **Similarity Score:** 1

      #### Item 92

        ## Documents

          ### Documents Details

          1. story_17583040_0
          2. story_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 93

        ## Documents

          ### Documents Details

          1. story_17583040_0
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 94

        ## Documents

          ### Documents Details

          1. story_17583040_0
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 95

        ## Documents

          ### Documents Details

          1. story_17583040_0
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 96

        ## Documents

          ### Documents Details

          1. story_17583040_1
          2. story_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 97

        ## Documents

          ### Documents Details

          1. story_17583040_1
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 98

        ## Documents

          ### Documents Details

          1. story_17583040_1
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 99

        ## Documents

          ### Documents Details

          1. story_17583040_2
          2. story_17583040_3

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 100

        ## Documents

          ### Documents Details

          1. story_17583040_2
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1

      #### Item 101

        ## Documents

          ### Documents Details

          1. rfc_17583040_0
          2. rfc_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. rfc
          2. e-commerce
          3. proposal

        - **Similarity Score:** 1

      #### Item 102

        ## Documents

          ### Documents Details

          1. meeting_17583040_0
          2. meeting_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. meeting
          2. notes
          3. e-commerce

        - **Similarity Score:** 1

      #### Item 103

        ## Documents

          ### Documents Details

          1. testplan_17583040_0
          2. testplan_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. plan
          2. e-commerce
          3. test

        - **Similarity Score:** 1

      #### Item 104

        ## Documents

          ### Documents Details

          1. deploy_17583040_0
          2. deploy_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. deploy
          2. e-commerce
          3. guide

        - **Similarity Score:** 1

      #### Item 105

        ## Documents

          ### Documents Details

          1. bug_17583040_0
          2. bug_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. bug
          2. jira
          3. e-commerce

        - **Similarity Score:** 1

      #### Item 106

        ## Documents

          ### Documents Details

          1. bug_17583040_0
          2. bug_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. bug
          2. jira
          3. e-commerce

        - **Similarity Score:** 1

      #### Item 107

        ## Documents

          ### Documents Details

          1. bug_17583040_1
          2. bug_17583040_2

        ## Shared Tags

          ### Shared Tags Details

          1. bug
          2. jira
          3. e-commerce

        - **Similarity Score:** 1

      #### Item 108

        ## Documents

          ### Documents Details

          1. api_17583040_0
          2. api_17583040_1

        ## Shared Tags

          ### Shared Tags Details

          1. api
          2. documentation
          3. e-commerce
          4. rest

        - **Similarity Score:** 1

      #### Item 109

        ## Documents

          ### Documents Details

          1. story_17583040_3
          2. story_17583040_4

        ## Shared Tags

          ### Shared Tags Details

          1. user_story
          2. e-commerce
          3. next.js

        - **Similarity Score:** 1


    ## Category Relationships

      ## Architecture

        ### Architecture Details

        1. conf_architecture_17583040_0

      ## Api

        ### Api Details

        1. conf_api_17583040_1
        2. api_17583040_0
        3. api_17583040_1

      ## Design

        ### Design Details

        1. conf_design_17583040_2

      ## Requirements

        ### Requirements Details

        1. conf_requirements_17583040_3

      ## Security

        ### Security Details

        1. conf_security_17583040_4

      ## Testing

        ### Testing Details

        1. conf_testing_17583040_5
        2. testplan_17583040_0
        3. testplan_17583040_1

      ## Deployment

        ### Deployment Details

        1. conf_deployment_17583040_6
        2. deploy_17583040_0
        3. deploy_17583040_1

      ## Feature

        ### Feature Details

        1. jira_feature_17583040_0
        2. jira_feature_17583040_2
        3. jira_feature_17583040_3

      ## Bug

        ### Bug Details

        1. jira_bug_17583040_1
        2. bug_17583040_0
        3. bug_17583040_1
        4. bug_17583040_2

      ## User Story

        ### User Story Details

        1. jira_user_story_17583040_4
        2. story_17583040_0
        3. story_17583040_1
        4. story_17583040_2
        5. story_17583040_3
        6. story_17583040_4

      ## Development

        ### Development Details

        1. pr_17583040_0
        2. pr_17583040_1
        3. pr_17583040_2

      ## Rfc

        ### Rfc Details

        1. rfc_17583040_0
        2. rfc_17583040_1

      ## Meeting Notes

        ### Meeting Notes Details

        1. meeting_17583040_0
        2. meeting_17583040_1


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

      1. rfc_17583040_0
      2. jira_bug_17583040_1
      3. jira_feature_17583040_0
      4. bug_17583040_2
      5. jira_feature_17583040_3
      6. bug_17583040_0
      7. conf_api_17583040_1
      8. meeting_17583040_0
      9. deploy_17583040_1
      10. pr_17583040_1
      11. conf_deployment_17583040_6
      12. bug_17583040_1
      13. api_17583040_0
      14. testplan_17583040_1
      15. pr_17583040_2
      16. story_17583040_4
      17. conf_requirements_17583040_3
      18. conf_testing_17583040_5
      19. pr_17583040_0
      20. conf_design_17583040_2
      21. jira_user_story_17583040_4
      22. conf_security_17583040_4
      23. api_17583040_1
      24. meeting_17583040_1
      25. jira_feature_17583040_2
      26. story_17583040_1
      27. testplan_17583040_0
      28. rfc_17583040_1
      29. story_17583040_3
      30. deploy_17583040_0
      31. story_17583040_0
      32. story_17583040_2
      33. conf_architecture_17583040_0

    ## Creation Dates

      ### Creation Dates Details

      1. 2025-08-22T05:04:03.803221
      2. 2025-08-30T02:09:03.803221
      3. 2025-08-30T23:34:03.803221
      4. 2025-09-04T02:01:03.803221
      5. 2025-09-05T23:06:03.803221
      6. 2025-09-06T06:57:03.803221
      7. 2025-09-06T22:17:03.803221
      8. 2025-09-07T01:31:03.803221
      9. 2025-09-10T08:32:03.803221
      10. 2025-09-10T17:04:03.803221
      11. 2025-09-11T04:03:03.803221
      12. 2025-09-11T10:44:03.803221
      13. 2025-09-11T22:16:03.803221
      14. 2025-09-13T03:35:03.803221
      15. 2025-09-13T03:53:03.803221
      16. 2025-09-13T07:54:03.803221
      17. 2025-09-14T02:29:03.803221
      18. 2025-09-14T06:46:03.803221
      19. 2025-09-15T04:51:03.803221
      20. 2025-09-15T15:56:03.803221
      21. 2025-09-15T18:45:03.803221
      22. 2025-09-16T09:18:03.803221
      23. 2025-09-16T20:34:03.803221
      24. 2025-09-17T08:49:03.803221
      25. 2025-09-17T14:28:03.803221
      26. 2025-09-17T15:47:03.803221
      27. 2025-09-17T17:26:03.803221
      28. 2025-09-17T23:16:03.803221
      29. 2025-09-17T23:18:03.803221
      30. 2025-09-18T01:37:03.803221
      31. 2025-09-18T05:37:03.803221
      32. 2025-09-18T10:04:03.803221
      33. 2025-09-18T22:13:03.803221

    ## Category Evolution

      ## Rfc

        ### Rfc Details

        1. rfc_17583040_0
        2. rfc_17583040_1

      ## Bug

        ### Bug Details

        1. jira_bug_17583040_1
        2. bug_17583040_2
        3. bug_17583040_0
        4. bug_17583040_1

      ## Feature

        ### Feature Details

        1. jira_feature_17583040_0
        2. jira_feature_17583040_3
        3. jira_feature_17583040_2

      ## Api

        ### Api Details

        1. conf_api_17583040_1
        2. api_17583040_0
        3. api_17583040_1

      ## Meeting Notes

        ### Meeting Notes Details

        1. meeting_17583040_0
        2. meeting_17583040_1

      ## Deployment

        ### Deployment Details

        1. deploy_17583040_1
        2. conf_deployment_17583040_6
        3. deploy_17583040_0

      ## Development

        ### Development Details

        1. pr_17583040_1
        2. pr_17583040_2
        3. pr_17583040_0

      ## Testing

        ### Testing Details

        1. testplan_17583040_1
        2. conf_testing_17583040_5
        3. testplan_17583040_0

      ## User Story

        ### User Story Details

        1. story_17583040_4
        2. jira_user_story_17583040_4
        3. story_17583040_1
        4. story_17583040_3
        5. story_17583040_0
        6. story_17583040_2

      ## Requirements

        ### Requirements Details

        1. conf_requirements_17583040_3

      ## Design

        ### Design Details

        1. conf_design_17583040_2

      ## Security

        ### Security Details

        1. conf_security_17583040_4

      ## Architecture

        ### Architecture Details

        1. conf_architecture_17583040_0




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

        1. conf_architecture_17583040_0
        2. conf_api_17583040_1

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
Generated: 2025-09-19 12:48:04

## Summary
- Total Documents: 33
- Document Types: confluence, user_story, deployment_guide, rfc, test_plan, jira, meeting_notes, pr

## Documents by Type


### CONFLUENCE Documents (9)

#### 1. E-Commerce Platform - System Architecture

**ID:** conf_architecture_17583040_0
**Author:** Sarah Johnson
**Created:** 2025-09-18T22:13:03.803221
**Updated:** 2025-09-18T05:16:03.803221
**Status:** published
**Category:** architecture
**Tags:** architecture, e-commerce, next.js, rust

**Content:**
```
# E-Commerce Platform Architecture

## Overview
The e-commerce platform is built on microservices architecture for scalability and resilience.

## Core Components
- **User Management Service**: Handles authentication, SSO, and user profiles
- **Business Logic Engine**: Implements core e-commerce domain logic with robust validation
- **Data Processing Service**: Real-time analytics, ETL pipelines, and reporting
- **Notification Service**: Asynchronous event-driven notifications (email, SMS, webhooks)

## Technology Stack
- Frontend: Next.js (SPA, SSR, PWA support)
- Backend: Rust (REST & GraphQL APIs)
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

#### 2. API Documentation - E-Commerce Endpoint 3

**ID:** api_17583040_1
**Author:** Sarah Johnson
**Created:** 2025-09-16T20:34:03.803221
**Updated:** 2025-09-17T11:45:03.803221
**Status:** published
**Category:** api
**Tags:** api, documentation, rest, e-commerce

**Content:**
```
# API Endpoint 3

## Method
POST /api/v1/e-commerce/endpoint3

## Description
Retrieves an entity.

## Request/Response
```json
{ "id": "abc1", "result": "ok" }
```

```

#### 3. Security Overview - E-Commerce Platform

**ID:** conf_security_17583040_4
**Author:** Lisa Rodriguez
**Created:** 2025-09-16T09:18:03.803221
**Updated:** 2025-09-16T23:34:03.803221
**Status:** published
**Category:** security
**Tags:** security, e-commerce, next.js, rust

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

#### 4. Design Document - E-Commerce Notifications

**ID:** conf_design_17583040_2
**Author:** Sarah Johnson
**Created:** 2025-09-15T15:56:03.803221
**Updated:** 2025-09-18T23:13:03.803221
**Status:** published
**Category:** design
**Tags:** design, e-commerce, next.js, rust

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

#### 5. Testing Strategy - E-Commerce Platform

**ID:** conf_testing_17583040_5
**Author:** David Kim
**Created:** 2025-09-14T06:46:03.803221
**Updated:** 2025-09-17T22:03:03.803221
**Status:** published
**Category:** testing
**Tags:** testing, e-commerce, next.js, rust

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

#### 6. Requirements Specification - E-Commerce Onboarding

**ID:** conf_requirements_17583040_3
**Author:** John Doe
**Created:** 2025-09-14T02:29:03.803221
**Updated:** 2025-09-17T23:14:03.803221
**Status:** published
**Category:** requirements
**Tags:** requirements, e-commerce, next.js, rust

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

#### 7. API Documentation - E-Commerce Endpoint 2

**ID:** api_17583040_0
**Author:** Emma Wilson
**Created:** 2025-09-11T22:16:03.803221
**Updated:** 2025-09-17T17:07:03.803221
**Status:** published
**Category:** api
**Tags:** api, documentation, rest, e-commerce

**Content:**
```
# API Endpoint 2

## Method
POST /api/v1/e-commerce/endpoint2

## Description
Retrieves an entity.

## Request/Response
```json
{ "id": "abc0", "result": "ok" }
```

```

#### 8. Deployment Guide - E-Commerce Platform

**ID:** conf_deployment_17583040_6
**Author:** Priya Patel
**Created:** 2025-09-11T04:03:03.803221
**Updated:** 2025-09-16T23:04:03.803221
**Status:** published
**Category:** deployment
**Tags:** deployment, e-commerce, next.js, rust

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

#### 9. API Documentation - E-Commerce Service

**ID:** conf_api_17583040_1
**Author:** Lisa Rodriguez
**Created:** 2025-09-06T22:17:03.803221
**Updated:** 2025-09-17T17:29:03.803221
**Status:** published
**Category:** api
**Tags:** api, e-commerce, next.js, rust

**Content:**
```
# E-Commerce Service API

## Overview
RESTful and GraphQL APIs for e-commerce platform operations.

## Authentication
All API requests require JWT token authentication and API key header.

## Endpoints
### GET /api/v1/e_commerce/items
Retrieves a list of e-commerce items.

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

### POST /api/v1/e_commerce/items
Creates a new item.

**Request Body:**
```json
{
  "name": "New Item",
  "description": "Detailed description."
}
```

```


### USER_STORY Documents (5)

#### 1. User Story: As a user...

**ID:** story_17583040_2
**Author:** Sarah Johnson
**Created:** 2025-09-18T10:04:03.803221
**Updated:** 2025-09-19T11:21:03.803221
**Status:** closed
**Category:** user_story
**Tags:** user_story, e-commerce, next.js

**Content:**
```
As a developer, I want to export data so that I can increase security.

## Acceptance Criteria
- Email notifications
- Audit logs

```

#### 2. User Story: As a developer...

**ID:** story_17583040_0
**Author:** Sarah Johnson
**Created:** 2025-09-18T05:37:03.803221
**Updated:** 2025-09-19T11:57:03.803221
**Status:** open
**Category:** user_story
**Tags:** user_story, e-commerce, next.js

**Content:**
```
As a developer, I want to reset password so that I can get timely alerts.

## Acceptance Criteria
- Custom widgets
- Audit logs

```

#### 3. User Story: As a user, I can receive alerts

**ID:** story_17583040_3
**Author:** Alex Thompson
**Created:** 2025-09-17T23:18:03.803221
**Updated:** 2025-09-18T09:04:03.803221
**Status:** open
**Category:** user_story
**Tags:** user_story, e-commerce, next.js

**Content:**
```
As a user, I want to filter data so that I can customize experience.

## Acceptance Criteria
- Filter by date
- Accessible

```

#### 4. User Story: As an admin...

**ID:** story_17583040_1
**Author:** Jane Smith
**Created:** 2025-09-17T15:47:03.803221
**Updated:** 2025-09-18T06:08:03.803221
**Status:** review
**Category:** user_story
**Tags:** user_story, e-commerce, next.js

**Content:**
```
As a admin, I want to export data so that I can increase security.

## Acceptance Criteria
- Email notifications
- Accessible UI

```

#### 5. User Story: As a user, I can receive alerts

**ID:** story_17583040_4
**Author:** Lisa Rodriguez
**Created:** 2025-09-13T07:54:03.803221
**Updated:** 2025-09-18T22:08:03.803221
**Status:** review
**Category:** user_story
**Tags:** user_story, e-commerce, next.js

**Content:**
```
As a user, I want to receive alerts so that I can customize experience.

## Acceptance Criteria
- Filter by date
- Accessible

```


### DEPLOYMENT_GUIDE Documents (2)

#### 1. Deployment Guide: E-Commerce Production

**ID:** deploy_17583040_0
**Author:** Alex Thompson
**Created:** 2025-09-18T01:37:03.803221
**Updated:** 2025-09-17T06:10:03.803221
**Status:** published
**Category:** deployment
**Tags:** deploy, guide, e-commerce

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

#### 2. Deployment Guide: E-Commerce Staging

**ID:** deploy_17583040_1
**Author:** Lisa Rodriguez
**Created:** 2025-09-10T08:32:03.803221
**Updated:** 2025-09-18T05:37:03.803221
**Status:** published
**Category:** deployment
**Tags:** deploy, guide, e-commerce

**Content:**
```
# Deployment Guide

## Environment
- Dev

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

**ID:** rfc_17583040_1
**Author:** Alex Thompson
**Created:** 2025-09-17T23:16:03.803221
**Updated:** 2025-09-18T06:33:03.803221
**Status:** open
**Category:** rfc
**Tags:** rfc, proposal, e-commerce

**Content:**
```
# RFC: Adopt OpenAPI

## Motivation
Standardize API schema

## Proposal
- Adopt OpenAPI 3.0
- Update documentation
- Provide migration plan

## Drawbacks
- Migration effort

## Alternatives
- Keep current approach
- Evaluate other tools

```

#### 2. RFC: Migrate to Kubernetes

**ID:** rfc_17583040_0
**Author:** Sarah Johnson
**Created:** 2025-08-22T05:04:03.803221
**Updated:** 2025-09-16T21:23:03.803221
**Status:** open
**Category:** rfc
**Tags:** rfc, proposal, e-commerce

**Content:**
```
# RFC: Adopt OpenAPI

## Motivation
Standardize API schema

## Proposal
- Migrate deployment to Kubernetes
- Update documentation
- Provide migration plan

## Drawbacks
- Migration effort

## Alternatives
- Keep current approach
- Evaluate other tools

```


### TEST_PLAN Documents (2)

#### 1. Test Plan: E-Commerce Authentication

**ID:** testplan_17583040_0
**Author:** Jane Smith
**Created:** 2025-09-17T17:26:03.803221
**Updated:** 2025-09-16T19:08:03.803221
**Status:** published
**Category:** testing
**Tags:** test, plan, e-commerce

**Content:**
```
# Test Plan

## Scope
- Authentication module

## Objectives
- Validate access control

## Test Cases
- UI is accessible
- Session timeout

## Tooling
- Postman

## Exit Criteria
- 100% test pass

```

#### 2. Test Plan: E-Commerce Authentication

**ID:** testplan_17583040_1
**Author:** David Kim
**Created:** 2025-09-13T03:35:03.803221
**Updated:** 2025-09-17T06:35:03.803221
**Status:** published
**Category:** testing
**Tags:** test, plan, e-commerce

**Content:**
```
# Test Plan

## Scope
- UI module

## Objectives
- Validate input validation

## Test Cases
- Login with valid/invalid credentials
- Error messages

## Tooling
- Postman

## Exit Criteria
- 100% test pass

```


### JIRA Documents (8)

#### 1. Epic: E-Commerce Mobile App Launch

**ID:** jira_feature_17583040_2
**Author:** Sarah Johnson
**Created:** 2025-09-17T14:28:03.803221
**Updated:** 2025-09-14T07:58:03.803221
**Status:** open
**Category:** feature
**Tags:** feature, high, jira, e-commerce
**Assignee:** Sarah Johnson
**Priority:** high

**Content:**
```
Epic to track all work for mobile app launch.

## Child Issues
- JIRA-123: Mobile UI
- JIRA-124: API integration
- JIRA-125: Push notifications
```

#### 2. Story: As a user, I can reset my password via email

**ID:** jira_user_story_17583040_4
**Author:** Alex Thompson
**Created:** 2025-09-15T18:45:03.803221
**Updated:** 2025-09-17T11:52:03.803221
**Status:** resolved
**Category:** user_story
**Tags:** user_story, high, jira, e-commerce
**Assignee:** Alex Thompson
**Priority:** high

**Content:**
```
User should be able to request password reset and receive a secure email link.

## Acceptance Criteria
- Email sent to user
- Link expires in 30 minutes
- Password complexity enforced
```

#### 3. Bug: E-Commerce - Login failure

**ID:** bug_17583040_1
**Author:** John Doe
**Created:** 2025-09-11T10:44:03.803221
**Updated:** 2025-09-14T04:13:03.803221
**Status:** resolved
**Category:** bug
**Tags:** bug, jira, e-commerce
**Assignee:** Priya Patel
**Priority:** critical

**Content:**
```
Steps to Reproduce:
1. Login with invalid credentials
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

#### 4. Bug: E-Commerce - Login failure

**ID:** bug_17583040_0
**Author:** Priya Patel
**Created:** 2025-09-06T06:57:03.803221
**Updated:** 2025-09-17T18:26:03.803221
**Status:** in_progress
**Category:** bug
**Tags:** bug, jira, e-commerce
**Assignee:** Priya Patel
**Priority:** high

**Content:**
```
Steps to Reproduce:
1. Submit large file
2. Observe error

## Expected
Timeout handled

## Actual
UI freezes

## Logs
```
[stacktrace]
```

```

#### 5. Task: Refactor Rust Service Layer

**ID:** jira_feature_17583040_3
**Author:** Priya Patel
**Created:** 2025-09-05T23:06:03.803221
**Updated:** 2025-09-19T03:10:03.803221
**Status:** review
**Category:** feature
**Tags:** feature, medium, jira, e-commerce
**Assignee:** Alex Thompson
**Priority:** medium

**Content:**
```
Refactor service layer for maintainability and testability.

## Subtasks
- Add unit tests
- Extract business logic
- Update documentation
```

#### 6. Bug: E-Commerce - Timeout error

**ID:** bug_17583040_2
**Author:** David Kim
**Created:** 2025-09-04T02:01:03.803221
**Updated:** 2025-09-17T08:03:03.803221
**Status:** in_progress
**Category:** bug
**Tags:** bug, jira, e-commerce
**Assignee:** Alex Thompson
**Priority:** critical

**Content:**
```
Steps to Reproduce:
1. Submit large file
2. Observe error

## Expected
No crash

## Actual
500 Internal Server Error

## Logs
```
[stacktrace]
```

```

#### 7. Implement Advanced E-Commerce Dashboard

**ID:** jira_feature_17583040_0
**Author:** Jane Smith
**Created:** 2025-08-30T23:34:03.803221
**Updated:** 2025-09-18T17:41:03.803221
**Status:** in_progress
**Category:** feature
**Tags:** feature, high, jira, e-commerce
**Assignee:** Priya Patel
**Priority:** high

**Content:**
```
As a product manager, I want an advanced dashboard so I can track e-commerce platform metrics.

## Acceptance Criteria
- Real-time metrics
- Next.js frontend
- Rust backend API
- Mobile-responsive
```

#### 8. Bug: E-Commerce API returns 500 on POST /items

**ID:** jira_bug_17583040_1
**Author:** David Kim
**Created:** 2025-08-30T02:09:03.803221
**Updated:** 2025-09-15T15:47:03.803221
**Status:** open
**Category:** bug
**Tags:** bug, critical, jira, e-commerce
**Assignee:** Alex Thompson
**Priority:** critical

**Content:**
```
Steps to Reproduce:
1. POST to /api/v1/e-commerce/items with invalid payload
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


### MEETING_NOTES Documents (2)

#### 1. Meeting Notes: Design Review

**ID:** meeting_17583040_1
**Author:** Mike Chen
**Created:** 2025-09-17T08:49:03.803221
**Updated:** 2025-09-18T17:02:03.803221
**Status:** published
**Category:** meeting_notes
**Tags:** meeting, notes, e-commerce

**Content:**
```
# Meeting Notes

**Date:** 2025-09-17T17:50:03.803221
**Attendees:** Jane Smith, Emma Wilson, Lisa Rodriguez, Sarah Johnson

## Agenda
- Review sprint goals
- Architecture discussion

## Notes
- Identified key technical debt
- Follow up with DevOps

## Action Items
- Prepare demo

```

#### 2. Meeting Notes: Sprint Planning

**ID:** meeting_17583040_0
**Author:** Priya Patel
**Created:** 2025-09-07T01:31:03.803221
**Updated:** 2025-09-19T06:26:03.803221
**Status:** published
**Category:** meeting_notes
**Tags:** meeting, notes, e-commerce

**Content:**
```
# Meeting Notes

**Date:** 2025-09-15T06:26:03.803221
**Attendees:** John Doe, David Kim, Priya Patel, Mike Chen

## Agenda
- Demo new features
- Q&A

## Notes
- Action items assigned
- Follow up with DevOps

## Action Items
- Fix critical bug

```


### PR Documents (3)

#### 1. PR: E-Commerce - Bugfix #489

**ID:** pr_17583040_0
**Author:** Alex Thompson
**Created:** 2025-09-15T04:51:03.803221
**Updated:** 2025-09-17T05:58:03.803221
**Status:** merged
**Category:** development
**Tags:** pr, github, review, e-commerce

**Content:**
```
## Description
Implements bugfix for e-commerce module.

## Changes
- Updated authentication logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-911

```

#### 2. PR: E-Commerce - Feature #426

**ID:** pr_17583040_2
**Author:** Mike Chen
**Created:** 2025-09-13T03:53:03.803221
**Updated:** 2025-09-18T03:52:03.803221
**Status:** review
**Category:** development
**Tags:** pr, github, review, e-commerce

**Content:**
```
## Description
Implements bugfix for e-commerce module.

## Changes
- Updated UI logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-280

```

#### 3. PR: E-Commerce - Bugfix #511

**ID:** pr_17583040_1
**Author:** Mike Chen
**Created:** 2025-09-10T17:04:03.803221
**Updated:** 2025-09-19T00:35:03.803221
**Status:** merged
**Category:** development
**Tags:** pr, github, review, e-commerce

**Content:**
```
## Description
Implements bugfix for e-commerce module.

## Changes
- Updated authentication logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-262

```


  ## Metadata

    - **Generated At:** 2025-09-19T12:48:04.168119
    - **Total Documents:** 33
    ## Document Types

      ### Document Types Details

      1. confluence
      2. user_story
      3. deployment_guide
      4. rfc
      5. test_plan
      6. jira
      7. meeting_notes
      8. pr

    - **Sorted By:** dateCreated
    - **Sort Order:** desc



