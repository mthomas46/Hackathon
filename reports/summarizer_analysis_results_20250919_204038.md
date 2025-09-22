# 📊 Comprehensive Analysis Results Report

**Report Generated:** 2025-09-19 20:40:38 UTC
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

    - **Document Id:** conf_architecture_17583324_0
    - **Title:** Education Platform - System Architecture
    - **Category:** architecture
    ## Tags

      ### Tags Details

      1. architecture
      2. education
      3. vue.js
      4. python

    - **Summary:** # Education Platform Architecture

## Overview
The education platform is built on microservices architecture for scalability and resilience.

## Core Components
- **User Management Service**: Handles authentication, SSO, and user profiles
- **Business Logic Engine**: Implements core education domain logic with robust validation
- **Data Processing Service**: Real-time analytics, ETL pipelines, and reporting
- **Notification Service**: Asynchronous event-driven notifications (email, SMS, webhooks)

## Technology Stack
- Frontend: Vue.js (SPA, SSR, PWA support)
- Backend: Python (REST & GraphQL APIs)
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

    - **Document Id:** conf_api_17583324_1
    - **Title:** API Documentation - Education Service
    - **Category:** api
    ## Tags

      ### Tags Details

      1. api
      2. education
      3. vue.js
      4. python

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

    - **Document Id:** conf_design_17583324_2
    - **Title:** Design Document - Education Notifications
    - **Category:** design
    ## Tags

      ### Tags Details

      1. design
      2. education
      3. vue.js
      4. python

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

    - **Document Id:** conf_requirements_17583324_3
    - **Title:** Requirements Specification - Education Onboarding
    - **Category:** requirements
    ## Tags

      ### Tags Details

      1. requirements
      2. education
      3. vue.js
      4. python

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

    - **Document Id:** conf_security_17583324_4
    - **Title:** Security Overview - Education Platform
    - **Category:** security
    ## Tags

      ### Tags Details

      1. security
      2. education
      3. vue.js
      4. python

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

    - **Document Id:** conf_testing_17583324_5
    - **Title:** Testing Strategy - Education Platform
    - **Category:** testing
    ## Tags

      ### Tags Details

      1. testing
      2. education
      3. vue.js
      4. python

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

    - **Document Id:** conf_deployment_17583324_6
    - **Title:** Deployment Guide - Education Platform
    - **Category:** deployment
    ## Tags

      ### Tags Details

      1. deployment
      2. education
      3. vue.js
      4. python

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

    - **Document Id:** jira_feature_17583324_0
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
- Vue.js frontend
- Python backend API
- Mobile-responsive
    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 9

    - **Document Id:** jira_bug_17583324_1
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

    - **Document Id:** jira_feature_17583324_2
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

    - **Document Id:** jira_feature_17583324_3
    - **Title:** Task: Refactor Python Service Layer
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

    - **Document Id:** jira_user_story_17583324_4
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

    - **Document Id:** pr_17583324_0
    - **Title:** PR: Education - Bugfix #212
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
- Updated UI logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-198

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 14

    - **Document Id:** pr_17583324_1
    - **Title:** PR: Education - Feature #397
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
- JIRA-332

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 15

    - **Document Id:** pr_17583324_2
    - **Title:** PR: Education - Feature #589
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
- Updated UI logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-809

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 16

    - **Document Id:** story_17583324_0
    - **Title:** User Story: As a developer...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. vue.js

    - **Summary:** As a user, I want to export data so that I can improve productivity.

## Acceptance Criteria
- Email notifications
- Accessible UI

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 17

    - **Document Id:** story_17583324_1
    - **Title:** User Story: As an admin...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. vue.js

    - **Summary:** As a developer, I want to export data so that I can get timely alerts.

## Acceptance Criteria
- Custom widgets
- Accessible UI

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 18

    - **Document Id:** story_17583324_2
    - **Title:** User Story: As a user...
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. vue.js

    - **Summary:** As a admin, I want to receive notifications so that I can increase security.

## Acceptance Criteria
- Export as CSV
- Audit logs

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 19

    - **Document Id:** rfc_17583324_0
    - **Title:** RFC: Adopt OpenAPI
    - **Category:** rfc
    ## Tags

      ### Tags Details

      1. rfc
      2. proposal
      3. education

    - **Summary:** # RFC: Adopt OpenAPI

## Motivation
Improve developer experience

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

  #### Item 20

    - **Document Id:** rfc_17583324_1
    - **Title:** RFC: Adopt OpenAPI
    - **Category:** rfc
    ## Tags

      ### Tags Details

      1. rfc
      2. proposal
      3. education

    - **Summary:** # RFC: Switch to GraphQL

## Motivation
Improve developer experience

## Proposal
- Adopt OpenAPI 3.0
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

  #### Item 21

    - **Document Id:** meeting_17583324_0
    - **Title:** Meeting Notes: Sprint Planning
    - **Category:** meeting_notes
    ## Tags

      ### Tags Details

      1. meeting
      2. notes
      3. education

    - **Summary:** # Meeting Notes

**Date:** 2025-09-11T19:04:38.488976
**Attendees:** Lisa Rodriguez, David Kim, Sarah Johnson, Mike Chen

## Agenda
- Review sprint goals
- Architecture discussion

## Notes
- Action items assigned
- Follow up with DevOps

## Action Items
- Update documentation

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 22

    - **Document Id:** meeting_17583324_1
    - **Title:** Meeting Notes: Retrospective
    - **Category:** meeting_notes
    ## Tags

      ### Tags Details

      1. meeting
      2. notes
      3. education

    - **Summary:** # Meeting Notes

**Date:** 2025-09-18T12:01:38.488976
**Attendees:** Sarah Johnson, Mike Chen, Jane Smith, Alex Thompson

## Agenda
- Demo new features
- Architecture discussion

## Notes
- Identified key technical debt
- Schedule security review

## Action Items
- Fix critical bug

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 23

    - **Document Id:** testplan_17583324_0
    - **Title:** Test Plan: Education UI
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
- Validate login

## Test Cases
- Login with valid/invalid credentials
- Password reset

## Tooling
- Cypress

## Exit Criteria
- 100% test pass

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 24

    - **Document Id:** testplan_17583324_1
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
- Validate token refresh

## Test Cases
- API returns correct status codes
- Session timeout

## Tooling
- Postman

## Exit Criteria
- 100% test pass

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 25

    - **Document Id:** deploy_17583324_0
    - **Title:** Deployment Guide: Education Dev
    - **Category:** deployment
    ## Tags

      ### Tags Details

      1. deploy
      2. guide
      3. education

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

  #### Item 26

    - **Document Id:** deploy_17583324_1
    - **Title:** Deployment Guide: Education Production
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

    - **Document Id:** bug_17583324_0
    - **Title:** Bug: Education - Login failure
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. jira
      3. education

    - **Summary:** Steps to Reproduce:
1. Submit large file
2. Observe error

## Expected
Graceful error message

## Actual
Timeout not handled

## Logs
```
[stacktrace]
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 28

    - **Document Id:** bug_17583324_1
    - **Title:** Bug: Education - Login failure
    - **Category:** bug
    ## Tags

      ### Tags Details

      1. bug
      2. jira
      3. education

    - **Summary:** Steps to Reproduce:
1. Submit large file
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

    - **Document Id:** bug_17583324_2
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

    - **Document Id:** api_17583324_0
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
PUT /api/v1/education/endpoint2

## Description
Deletes an entity.

## Request/Response
```json
{ "id": "abc0", "result": "ok" }
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 31

    - **Document Id:** api_17583324_1
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
Deletes an entity.

## Request/Response
```json
{ "id": "abc1", "result": "ok" }
```

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 32

    - **Document Id:** story_17583324_3
    - **Title:** User Story: As a user, I can filter data
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. vue.js

    - **Summary:** As a user, I want to filter data so that I can find relevant info.

## Acceptance Criteria
- Email alerts
- Accessible

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0

  #### Item 33

    - **Document Id:** story_17583324_4
    - **Title:** User Story: As a user, I can filter data
    - **Category:** user_story
    ## Tags

      ### Tags Details

      1. user_story
      2. education
      3. vue.js

    - **Summary:** As a user, I want to receive alerts so that I can stay informed.

## Acceptance Criteria
- Filter by date
- Accessible

    - **Category Detected:** Unknown
    - **Confidence:** 0
    - **Processing Time:** 0


## Multi Document Analysis

  ## Categories Found

    ### Categories Found Details

    1. meeting_notes
    2. design
    3. feature
    4. development
    5. bug
    6. testing
    7. user_story
    8. deployment
    9. rfc
    10. security
    11. architecture
    12. requirements
    13. api

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
      - **Vue.Js:** 12
      - **Python:** 7
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

          1. conf_architecture_17583324_0
          2. conf_api_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 2

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. conf_design_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 3

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. conf_requirements_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 4

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. conf_security_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 5

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. conf_testing_17583324_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 6

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. conf_deployment_17583324_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 7

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. story_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 8

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 9

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 10

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 11

        ## Documents

          ### Documents Details

          1. conf_architecture_17583324_0
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 12

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. conf_design_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 13

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. conf_requirements_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 14

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. conf_security_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 15

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. conf_testing_17583324_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 16

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. conf_deployment_17583324_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 17

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. story_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 18

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 19

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 20

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. api_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. api

        - **Similarity Score:** 0.5

      #### Item 21

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. api_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. api

        - **Similarity Score:** 0.5

      #### Item 22

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 23

        ## Documents

          ### Documents Details

          1. conf_api_17583324_1
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 24

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. conf_requirements_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 25

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. conf_security_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 26

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. conf_testing_17583324_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 27

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. conf_deployment_17583324_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 28

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. story_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 29

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 30

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 31

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 32

        ## Documents

          ### Documents Details

          1. conf_design_17583324_2
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 33

        ## Documents

          ### Documents Details

          1. conf_requirements_17583324_3
          2. conf_security_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 34

        ## Documents

          ### Documents Details

          1. conf_requirements_17583324_3
          2. conf_testing_17583324_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 35

        ## Documents

          ### Documents Details

          1. conf_requirements_17583324_3
          2. conf_deployment_17583324_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 36

        ## Documents

          ### Documents Details

          1. conf_requirements_17583324_3
          2. story_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 37

        ## Documents

          ### Documents Details

          1. conf_requirements_17583324_3
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 38

        ## Documents

          ### Documents Details

          1. conf_requirements_17583324_3
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 39

        ## Documents

          ### Documents Details

          1. conf_requirements_17583324_3
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 40

        ## Documents

          ### Documents Details

          1. conf_requirements_17583324_3
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 41

        ## Documents

          ### Documents Details

          1. conf_security_17583324_4
          2. conf_testing_17583324_5

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 42

        ## Documents

          ### Documents Details

          1. conf_security_17583324_4
          2. conf_deployment_17583324_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 43

        ## Documents

          ### Documents Details

          1. conf_security_17583324_4
          2. story_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 44

        ## Documents

          ### Documents Details

          1. conf_security_17583324_4
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 45

        ## Documents

          ### Documents Details

          1. conf_security_17583324_4
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 46

        ## Documents

          ### Documents Details

          1. conf_security_17583324_4
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 47

        ## Documents

          ### Documents Details

          1. conf_security_17583324_4
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 48

        ## Documents

          ### Documents Details

          1. conf_testing_17583324_5
          2. conf_deployment_17583324_6

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. python

        - **Similarity Score:** 0.75

      #### Item 49

        ## Documents

          ### Documents Details

          1. conf_testing_17583324_5
          2. story_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 50

        ## Documents

          ### Documents Details

          1. conf_testing_17583324_5
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 51

        ## Documents

          ### Documents Details

          1. conf_testing_17583324_5
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 52

        ## Documents

          ### Documents Details

          1. conf_testing_17583324_5
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 53

        ## Documents

          ### Documents Details

          1. conf_testing_17583324_5
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 54

        ## Documents

          ### Documents Details

          1. conf_deployment_17583324_6
          2. story_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 55

        ## Documents

          ### Documents Details

          1. conf_deployment_17583324_6
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 56

        ## Documents

          ### Documents Details

          1. conf_deployment_17583324_6
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 57

        ## Documents

          ### Documents Details

          1. conf_deployment_17583324_6
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 58

        ## Documents

          ### Documents Details

          1. conf_deployment_17583324_6
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js

        - **Similarity Score:** 0.5

      #### Item 59

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_0
          2. jira_bug_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 60

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_0
          2. jira_feature_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. high
          2. jira
          3. education
          4. feature

        - **Similarity Score:** 1

      #### Item 61

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_0
          2. jira_feature_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira
          3. feature

        - **Similarity Score:** 0.75

      #### Item 62

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_0
          2. jira_user_story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. high
          2. jira
          3. education

        - **Similarity Score:** 0.75

      #### Item 63

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_0
          2. bug_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 64

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_0
          2. bug_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 65

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_0
          2. bug_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 66

        ## Documents

          ### Documents Details

          1. jira_bug_17583324_1
          2. jira_feature_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 67

        ## Documents

          ### Documents Details

          1. jira_bug_17583324_1
          2. jira_feature_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 68

        ## Documents

          ### Documents Details

          1. jira_bug_17583324_1
          2. jira_user_story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 69

        ## Documents

          ### Documents Details

          1. jira_bug_17583324_1
          2. bug_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira
          3. bug

        - **Similarity Score:** 0.75

      #### Item 70

        ## Documents

          ### Documents Details

          1. jira_bug_17583324_1
          2. bug_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira
          3. bug

        - **Similarity Score:** 0.75

      #### Item 71

        ## Documents

          ### Documents Details

          1. jira_bug_17583324_1
          2. bug_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira
          3. bug

        - **Similarity Score:** 0.75

      #### Item 72

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_2
          2. jira_feature_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira
          3. feature

        - **Similarity Score:** 0.75

      #### Item 73

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_2
          2. jira_user_story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. high
          2. jira
          3. education

        - **Similarity Score:** 0.75

      #### Item 74

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_2
          2. bug_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 75

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_2
          2. bug_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 76

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_2
          2. bug_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 77

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_3
          2. jira_user_story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 78

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_3
          2. bug_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 79

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_3
          2. bug_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 80

        ## Documents

          ### Documents Details

          1. jira_feature_17583324_3
          2. bug_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 81

        ## Documents

          ### Documents Details

          1. jira_user_story_17583324_4
          2. story_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 82

        ## Documents

          ### Documents Details

          1. jira_user_story_17583324_4
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 83

        ## Documents

          ### Documents Details

          1. jira_user_story_17583324_4
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 84

        ## Documents

          ### Documents Details

          1. jira_user_story_17583324_4
          2. bug_17583324_0

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 85

        ## Documents

          ### Documents Details

          1. jira_user_story_17583324_4
          2. bug_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 86

        ## Documents

          ### Documents Details

          1. jira_user_story_17583324_4
          2. bug_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira

        - **Similarity Score:** 0.5

      #### Item 87

        ## Documents

          ### Documents Details

          1. jira_user_story_17583324_4
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 88

        ## Documents

          ### Documents Details

          1. jira_user_story_17583324_4
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. user_story

        - **Similarity Score:** 0.5

      #### Item 89

        ## Documents

          ### Documents Details

          1. pr_17583324_0
          2. pr_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. pr
          3. github
          4. review

        - **Similarity Score:** 1

      #### Item 90

        ## Documents

          ### Documents Details

          1. pr_17583324_0
          2. pr_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. pr
          3. github
          4. review

        - **Similarity Score:** 1

      #### Item 91

        ## Documents

          ### Documents Details

          1. pr_17583324_1
          2. pr_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. pr
          3. github
          4. review

        - **Similarity Score:** 1

      #### Item 92

        ## Documents

          ### Documents Details

          1. story_17583324_0
          2. story_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 93

        ## Documents

          ### Documents Details

          1. story_17583324_0
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 94

        ## Documents

          ### Documents Details

          1. story_17583324_0
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 95

        ## Documents

          ### Documents Details

          1. story_17583324_0
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 96

        ## Documents

          ### Documents Details

          1. story_17583324_1
          2. story_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 97

        ## Documents

          ### Documents Details

          1. story_17583324_1
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 98

        ## Documents

          ### Documents Details

          1. story_17583324_1
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 99

        ## Documents

          ### Documents Details

          1. story_17583324_2
          2. story_17583324_3

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 100

        ## Documents

          ### Documents Details

          1. story_17583324_2
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1

      #### Item 101

        ## Documents

          ### Documents Details

          1. rfc_17583324_0
          2. rfc_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. proposal
          3. rfc

        - **Similarity Score:** 1

      #### Item 102

        ## Documents

          ### Documents Details

          1. meeting_17583324_0
          2. meeting_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. meeting
          2. notes
          3. education

        - **Similarity Score:** 1

      #### Item 103

        ## Documents

          ### Documents Details

          1. testplan_17583324_0
          2. testplan_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. plan
          3. test

        - **Similarity Score:** 1

      #### Item 104

        ## Documents

          ### Documents Details

          1. deploy_17583324_0
          2. deploy_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. guide
          3. deploy

        - **Similarity Score:** 1

      #### Item 105

        ## Documents

          ### Documents Details

          1. bug_17583324_0
          2. bug_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira
          3. bug

        - **Similarity Score:** 1

      #### Item 106

        ## Documents

          ### Documents Details

          1. bug_17583324_0
          2. bug_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira
          3. bug

        - **Similarity Score:** 1

      #### Item 107

        ## Documents

          ### Documents Details

          1. bug_17583324_1
          2. bug_17583324_2

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. jira
          3. bug

        - **Similarity Score:** 1

      #### Item 108

        ## Documents

          ### Documents Details

          1. api_17583324_0
          2. api_17583324_1

        ## Shared Tags

          ### Shared Tags Details

          1. documentation
          2. api
          3. education
          4. rest

        - **Similarity Score:** 1

      #### Item 109

        ## Documents

          ### Documents Details

          1. story_17583324_3
          2. story_17583324_4

        ## Shared Tags

          ### Shared Tags Details

          1. education
          2. vue.js
          3. user_story

        - **Similarity Score:** 1


    ## Category Relationships

      ## Architecture

        ### Architecture Details

        1. conf_architecture_17583324_0

      ## Api

        ### Api Details

        1. conf_api_17583324_1
        2. api_17583324_0
        3. api_17583324_1

      ## Design

        ### Design Details

        1. conf_design_17583324_2

      ## Requirements

        ### Requirements Details

        1. conf_requirements_17583324_3

      ## Security

        ### Security Details

        1. conf_security_17583324_4

      ## Testing

        ### Testing Details

        1. conf_testing_17583324_5
        2. testplan_17583324_0
        3. testplan_17583324_1

      ## Deployment

        ### Deployment Details

        1. conf_deployment_17583324_6
        2. deploy_17583324_0
        3. deploy_17583324_1

      ## Feature

        ### Feature Details

        1. jira_feature_17583324_0
        2. jira_feature_17583324_2
        3. jira_feature_17583324_3

      ## Bug

        ### Bug Details

        1. jira_bug_17583324_1
        2. bug_17583324_0
        3. bug_17583324_1
        4. bug_17583324_2

      ## User Story

        ### User Story Details

        1. jira_user_story_17583324_4
        2. story_17583324_0
        3. story_17583324_1
        4. story_17583324_2
        5. story_17583324_3
        6. story_17583324_4

      ## Development

        ### Development Details

        1. pr_17583324_0
        2. pr_17583324_1
        3. pr_17583324_2

      ## Rfc

        ### Rfc Details

        1. rfc_17583324_0
        2. rfc_17583324_1

      ## Meeting Notes

        ### Meeting Notes Details

        1. meeting_17583324_0
        2. meeting_17583324_1


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

      1. rfc_17583324_0
      2. rfc_17583324_1
      3. bug_17583324_0
      4. jira_feature_17583324_0
      5. conf_deployment_17583324_6
      6. pr_17583324_2
      7. conf_security_17583324_4
      8. pr_17583324_0
      9. bug_17583324_1
      10. pr_17583324_1
      11. jira_feature_17583324_3
      12. story_17583324_2
      13. jira_user_story_17583324_4
      14. jira_bug_17583324_1
      15. conf_design_17583324_2
      16. meeting_17583324_1
      17. story_17583324_0
      18. story_17583324_1
      19. conf_architecture_17583324_0
      20. conf_requirements_17583324_3
      21. conf_testing_17583324_5
      22. story_17583324_4
      23. bug_17583324_2
      24. api_17583324_0
      25. meeting_17583324_0
      26. testplan_17583324_1
      27. deploy_17583324_1
      28. testplan_17583324_0
      29. jira_feature_17583324_2
      30. story_17583324_3
      31. deploy_17583324_0
      32. api_17583324_1
      33. conf_api_17583324_1

    ## Creation Dates

      ### Creation Dates Details

      1. 2025-08-27T17:25:38.488976
      2. 2025-08-28T22:00:38.488976
      3. 2025-09-02T15:19:38.488976
      4. 2025-09-03T12:43:38.488976
      5. 2025-09-04T02:02:38.488976
      6. 2025-09-05T04:55:38.488976
      7. 2025-09-06T03:12:38.488976
      8. 2025-09-06T07:05:38.488976
      9. 2025-09-06T16:51:38.488976
      10. 2025-09-07T05:39:38.488976
      11. 2025-09-08T18:51:38.488976
      12. 2025-09-09T08:50:38.488976
      13. 2025-09-09T11:06:38.488976
      14. 2025-09-11T07:31:38.488976
      15. 2025-09-11T13:26:38.488976
      16. 2025-09-11T13:27:38.488976
      17. 2025-09-12T05:06:38.488976
      18. 2025-09-12T09:21:38.488976
      19. 2025-09-12T17:29:38.488976
      20. 2025-09-13T01:08:38.488976
      21. 2025-09-13T07:51:38.488976
      22. 2025-09-13T20:29:38.488976
      23. 2025-09-15T05:06:38.488976
      24. 2025-09-15T09:34:38.488976
      25. 2025-09-15T23:01:38.488976
      26. 2025-09-16T07:38:38.488976
      27. 2025-09-16T22:48:38.488976
      28. 2025-09-17T05:28:38.488976
      29. 2025-09-17T05:55:38.488976
      30. 2025-09-17T06:55:38.488976
      31. 2025-09-18T03:22:38.488976
      32. 2025-09-18T17:47:38.488976
      33. 2025-09-19T02:38:38.488976

    ## Category Evolution

      ## Rfc

        ### Rfc Details

        1. rfc_17583324_0
        2. rfc_17583324_1

      ## Bug

        ### Bug Details

        1. bug_17583324_0
        2. bug_17583324_1
        3. jira_bug_17583324_1
        4. bug_17583324_2

      ## Feature

        ### Feature Details

        1. jira_feature_17583324_0
        2. jira_feature_17583324_3
        3. jira_feature_17583324_2

      ## Deployment

        ### Deployment Details

        1. conf_deployment_17583324_6
        2. deploy_17583324_1
        3. deploy_17583324_0

      ## Development

        ### Development Details

        1. pr_17583324_2
        2. pr_17583324_0
        3. pr_17583324_1

      ## Security

        ### Security Details

        1. conf_security_17583324_4

      ## User Story

        ### User Story Details

        1. story_17583324_2
        2. jira_user_story_17583324_4
        3. story_17583324_0
        4. story_17583324_1
        5. story_17583324_4
        6. story_17583324_3

      ## Design

        ### Design Details

        1. conf_design_17583324_2

      ## Meeting Notes

        ### Meeting Notes Details

        1. meeting_17583324_1
        2. meeting_17583324_0

      ## Architecture

        ### Architecture Details

        1. conf_architecture_17583324_0

      ## Requirements

        ### Requirements Details

        1. conf_requirements_17583324_3

      ## Testing

        ### Testing Details

        1. conf_testing_17583324_5
        2. testplan_17583324_1
        3. testplan_17583324_0

      ## Api

        ### Api Details

        1. api_17583324_0
        2. api_17583324_1
        3. conf_api_17583324_1




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

        1. conf_architecture_17583324_0
        2. conf_api_17583324_1

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
Generated: 2025-09-19 20:40:38

## Summary
- Total Documents: 33
- Document Types: confluence, deployment_guide, user_story, jira, test_plan, meeting_notes, pr, rfc

## Documents by Type


### CONFLUENCE Documents (9)

#### 1. API Documentation - Education Service

**ID:** conf_api_17583324_1
**Author:** David Kim
**Created:** 2025-09-19T02:38:38.488976
**Updated:** 2025-09-19T14:23:38.488976
**Status:** published
**Category:** api
**Tags:** api, education, vue.js, python

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

**ID:** api_17583324_1
**Author:** Jane Smith
**Created:** 2025-09-18T17:47:38.488976
**Updated:** 2025-09-18T12:18:38.488976
**Status:** published
**Category:** api
**Tags:** api, documentation, rest, education

**Content:**
```
# API Endpoint 3

## Method
DELETE /api/v1/education/endpoint3

## Description
Deletes an entity.

## Request/Response
```json
{ "id": "abc1", "result": "ok" }
```

```

#### 3. API Documentation - Education Endpoint 2

**ID:** api_17583324_0
**Author:** Mike Chen
**Created:** 2025-09-15T09:34:38.488976
**Updated:** 2025-09-18T05:39:38.488976
**Status:** published
**Category:** api
**Tags:** api, documentation, rest, education

**Content:**
```
# API Endpoint 2

## Method
PUT /api/v1/education/endpoint2

## Description
Deletes an entity.

## Request/Response
```json
{ "id": "abc0", "result": "ok" }
```

```

#### 4. Testing Strategy - Education Platform

**ID:** conf_testing_17583324_5
**Author:** Alex Thompson
**Created:** 2025-09-13T07:51:38.488976
**Updated:** 2025-09-18T22:39:38.488976
**Status:** published
**Category:** testing
**Tags:** testing, education, vue.js, python

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

#### 5. Requirements Specification - Education Onboarding

**ID:** conf_requirements_17583324_3
**Author:** Emma Wilson
**Created:** 2025-09-13T01:08:38.488976
**Updated:** 2025-09-19T22:00:38.488976
**Status:** published
**Category:** requirements
**Tags:** requirements, education, vue.js, python

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

#### 6. Education Platform - System Architecture

**ID:** conf_architecture_17583324_0
**Author:** David Kim
**Created:** 2025-09-12T17:29:38.488976
**Updated:** 2025-09-17T13:37:38.488976
**Status:** published
**Category:** architecture
**Tags:** architecture, education, vue.js, python

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
- Frontend: Vue.js (SPA, SSR, PWA support)
- Backend: Python (REST & GraphQL APIs)
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

#### 7. Design Document - Education Notifications

**ID:** conf_design_17583324_2
**Author:** Mike Chen
**Created:** 2025-09-11T13:26:38.488976
**Updated:** 2025-09-19T20:20:38.488976
**Status:** published
**Category:** design
**Tags:** design, education, vue.js, python

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

#### 8. Security Overview - Education Platform

**ID:** conf_security_17583324_4
**Author:** John Doe
**Created:** 2025-09-06T03:12:38.488976
**Updated:** 2025-09-18T14:31:38.488976
**Status:** published
**Category:** security
**Tags:** security, education, vue.js, python

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

#### 9. Deployment Guide - Education Platform

**ID:** conf_deployment_17583324_6
**Author:** Priya Patel
**Created:** 2025-09-04T02:02:38.488976
**Updated:** 2025-09-19T06:11:38.488976
**Status:** published
**Category:** deployment
**Tags:** deployment, education, vue.js, python

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


### DEPLOYMENT_GUIDE Documents (2)

#### 1. Deployment Guide: Education Dev

**ID:** deploy_17583324_0
**Author:** Lisa Rodriguez
**Created:** 2025-09-18T03:22:38.488976
**Updated:** 2025-09-17T18:25:38.488976
**Status:** published
**Category:** deployment
**Tags:** deploy, guide, education

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

#### 2. Deployment Guide: Education Production

**ID:** deploy_17583324_1
**Author:** Sarah Johnson
**Created:** 2025-09-16T22:48:38.488976
**Updated:** 2025-09-19T08:15:38.488976
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


### USER_STORY Documents (5)

#### 1. User Story: As a user, I can filter data

**ID:** story_17583324_3
**Author:** Sarah Johnson
**Created:** 2025-09-17T06:55:38.488976
**Updated:** 2025-09-19T03:31:38.488976
**Status:** in_progress
**Category:** user_story
**Tags:** user_story, education, vue.js

**Content:**
```
As a user, I want to filter data so that I can find relevant info.

## Acceptance Criteria
- Email alerts
- Accessible

```

#### 2. User Story: As a user, I can filter data

**ID:** story_17583324_4
**Author:** Alex Thompson
**Created:** 2025-09-13T20:29:38.488976
**Updated:** 2025-09-18T10:13:38.488976
**Status:** published
**Category:** user_story
**Tags:** user_story, education, vue.js

**Content:**
```
As a user, I want to receive alerts so that I can stay informed.

## Acceptance Criteria
- Filter by date
- Accessible

```

#### 3. User Story: As an admin...

**ID:** story_17583324_1
**Author:** Mike Chen
**Created:** 2025-09-12T09:21:38.488976
**Updated:** 2025-09-19T04:56:38.488976
**Status:** closed
**Category:** user_story
**Tags:** user_story, education, vue.js

**Content:**
```
As a developer, I want to export data so that I can get timely alerts.

## Acceptance Criteria
- Custom widgets
- Accessible UI

```

#### 4. User Story: As a developer...

**ID:** story_17583324_0
**Author:** Lisa Rodriguez
**Created:** 2025-09-12T05:06:38.488976
**Updated:** 2025-09-18T19:16:38.488976
**Status:** closed
**Category:** user_story
**Tags:** user_story, education, vue.js

**Content:**
```
As a user, I want to export data so that I can improve productivity.

## Acceptance Criteria
- Email notifications
- Accessible UI

```

#### 5. User Story: As a user...

**ID:** story_17583324_2
**Author:** Mike Chen
**Created:** 2025-09-09T08:50:38.488976
**Updated:** 2025-09-18T02:52:38.488976
**Status:** closed
**Category:** user_story
**Tags:** user_story, education, vue.js

**Content:**
```
As a admin, I want to receive notifications so that I can increase security.

## Acceptance Criteria
- Export as CSV
- Audit logs

```


### JIRA Documents (8)

#### 1. Epic: Education Mobile App Launch

**ID:** jira_feature_17583324_2
**Author:** Mike Chen
**Created:** 2025-09-17T05:55:38.488976
**Updated:** 2025-09-14T14:04:38.488976
**Status:** open
**Category:** feature
**Tags:** feature, high, jira, education
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

#### 2. Bug: Education - UI crash

**ID:** bug_17583324_2
**Author:** David Kim
**Created:** 2025-09-15T05:06:38.488976
**Updated:** 2025-09-15T20:19:38.488976
**Status:** open
**Category:** bug
**Tags:** bug, jira, education
**Assignee:** Alex Thompson
**Priority:** high

**Content:**
```
Steps to Reproduce:
1. Navigate to dashboard
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

#### 3. Bug: Education API returns 500 on POST /items

**ID:** jira_bug_17583324_1
**Author:** Alex Thompson
**Created:** 2025-09-11T07:31:38.488976
**Updated:** 2025-09-17T12:40:38.488976
**Status:** open
**Category:** bug
**Tags:** bug, critical, jira, education
**Assignee:** David Kim
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

#### 4. Story: As a user, I can reset my password via email

**ID:** jira_user_story_17583324_4
**Author:** Sarah Johnson
**Created:** 2025-09-09T11:06:38.488976
**Updated:** 2025-09-14T08:38:38.488976
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

#### 5. Task: Refactor Python Service Layer

**ID:** jira_feature_17583324_3
**Author:** Lisa Rodriguez
**Created:** 2025-09-08T18:51:38.488976
**Updated:** 2025-09-15T23:01:38.488976
**Status:** review
**Category:** feature
**Tags:** feature, medium, jira, education
**Assignee:** Priya Patel
**Priority:** medium

**Content:**
```
Refactor service layer for maintainability and testability.

## Subtasks
- Add unit tests
- Extract business logic
- Update documentation
```

#### 6. Bug: Education - Login failure

**ID:** bug_17583324_1
**Author:** Priya Patel
**Created:** 2025-09-06T16:51:38.488976
**Updated:** 2025-09-15T20:24:38.488976
**Status:** resolved
**Category:** bug
**Tags:** bug, jira, education
**Assignee:** Sarah Johnson
**Priority:** high

**Content:**
```
Steps to Reproduce:
1. Submit large file
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

#### 7. Implement Advanced Education Dashboard

**ID:** jira_feature_17583324_0
**Author:** Jane Smith
**Created:** 2025-09-03T12:43:38.488976
**Updated:** 2025-09-19T18:55:38.488976
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
- Vue.js frontend
- Python backend API
- Mobile-responsive
```

#### 8. Bug: Education - Login failure

**ID:** bug_17583324_0
**Author:** David Kim
**Created:** 2025-09-02T15:19:38.488976
**Updated:** 2025-09-16T00:08:38.488976
**Status:** open
**Category:** bug
**Tags:** bug, jira, education
**Assignee:** David Kim
**Priority:** high

**Content:**
```
Steps to Reproduce:
1. Submit large file
2. Observe error

## Expected
Graceful error message

## Actual
Timeout not handled

## Logs
```
[stacktrace]
```

```


### TEST_PLAN Documents (2)

#### 1. Test Plan: Education UI

**ID:** testplan_17583324_0
**Author:** Jane Smith
**Created:** 2025-09-17T05:28:38.488976
**Updated:** 2025-09-18T14:40:38.488976
**Status:** published
**Category:** testing
**Tags:** test, plan, education

**Content:**
```
# Test Plan

## Scope
- API module

## Objectives
- Validate login

## Test Cases
- Login with valid/invalid credentials
- Password reset

## Tooling
- Cypress

## Exit Criteria
- 100% test pass

```

#### 2. Test Plan: Education UI

**ID:** testplan_17583324_1
**Author:** Lisa Rodriguez
**Created:** 2025-09-16T07:38:38.488976
**Updated:** 2025-09-19T09:42:38.488976
**Status:** published
**Category:** testing
**Tags:** test, plan, education

**Content:**
```
# Test Plan

## Scope
- UI module

## Objectives
- Validate token refresh

## Test Cases
- API returns correct status codes
- Session timeout

## Tooling
- Postman

## Exit Criteria
- 100% test pass

```


### MEETING_NOTES Documents (2)

#### 1. Meeting Notes: Sprint Planning

**ID:** meeting_17583324_0
**Author:** Priya Patel
**Created:** 2025-09-15T23:01:38.488976
**Updated:** 2025-09-18T04:10:38.488976
**Status:** published
**Category:** meeting_notes
**Tags:** meeting, notes, education

**Content:**
```
# Meeting Notes

**Date:** 2025-09-11T19:04:38.488976
**Attendees:** Lisa Rodriguez, David Kim, Sarah Johnson, Mike Chen

## Agenda
- Review sprint goals
- Architecture discussion

## Notes
- Action items assigned
- Follow up with DevOps

## Action Items
- Update documentation

```

#### 2. Meeting Notes: Retrospective

**ID:** meeting_17583324_1
**Author:** Lisa Rodriguez
**Created:** 2025-09-11T13:27:38.488976
**Updated:** 2025-09-18T02:27:38.488976
**Status:** published
**Category:** meeting_notes
**Tags:** meeting, notes, education

**Content:**
```
# Meeting Notes

**Date:** 2025-09-18T12:01:38.488976
**Attendees:** Sarah Johnson, Mike Chen, Jane Smith, Alex Thompson

## Agenda
- Demo new features
- Architecture discussion

## Notes
- Identified key technical debt
- Schedule security review

## Action Items
- Fix critical bug

```


### PR Documents (3)

#### 1. PR: Education - Feature #397

**ID:** pr_17583324_1
**Author:** Jane Smith
**Created:** 2025-09-07T05:39:38.488976
**Updated:** 2025-09-19T06:29:38.488976
**Status:** merged
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
- JIRA-332

```

#### 2. PR: Education - Bugfix #212

**ID:** pr_17583324_0
**Author:** Jane Smith
**Created:** 2025-09-06T07:05:38.488976
**Updated:** 2025-09-18T18:32:38.488976
**Status:** review
**Category:** development
**Tags:** pr, github, review, education

**Content:**
```
## Description
Implements feature for education module.

## Changes
- Updated UI logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-198

```

#### 3. PR: Education - Feature #589

**ID:** pr_17583324_2
**Author:** Alex Thompson
**Created:** 2025-09-05T04:55:38.488976
**Updated:** 2025-09-17T18:02:38.488976
**Status:** review
**Category:** development
**Tags:** pr, github, review, education

**Content:**
```
## Description
Implements feature for education module.

## Changes
- Updated UI logic
- Improved test coverage
- Updated documentation

## Reviewer Checklist
- [ ] Code builds
- [ ] Tests pass
- [ ] Docs updated

## Linked Issues
- JIRA-809

```


### RFC Documents (2)

#### 1. RFC: Adopt OpenAPI

**ID:** rfc_17583324_1
**Author:** Priya Patel
**Created:** 2025-08-28T22:00:38.488976
**Updated:** 2025-09-19T20:37:38.488976
**Status:** open
**Category:** rfc
**Tags:** rfc, proposal, education

**Content:**
```
# RFC: Switch to GraphQL

## Motivation
Improve developer experience

## Proposal
- Adopt OpenAPI 3.0
- Update documentation
- Provide migration plan

## Drawbacks
- Learning curve

## Alternatives
- Keep current approach
- Evaluate other tools

```

#### 2. RFC: Adopt OpenAPI

**ID:** rfc_17583324_0
**Author:** Emma Wilson
**Created:** 2025-08-27T17:25:38.488976
**Updated:** 2025-09-18T03:26:38.488976
**Status:** open
**Category:** rfc
**Tags:** rfc, proposal, education

**Content:**
```
# RFC: Adopt OpenAPI

## Motivation
Improve developer experience

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


  ## Metadata

    - **Generated At:** 2025-09-19T20:40:38.844614
    - **Total Documents:** 33
    ## Document Types

      ### Document Types Details

      1. confluence
      2. deployment_guide
      3. user_story
      4. jira
      5. test_plan
      6. meeting_notes
      7. pr
      8. rfc

    - **Sorted By:** dateCreated
    - **Sort Order:** desc



