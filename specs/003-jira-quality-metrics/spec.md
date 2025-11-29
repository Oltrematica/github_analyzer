# Feature Specification: Jira Quality Metrics Export

**Feature Branch**: `003-jira-quality-metrics`
**Created**: 2025-11-28
**Status**: Draft
**Input**: User description: "Enhance Jira export files with quality metrics: Cycle Time, Bug Ratio, Description Quality Score, Comments per Issue, Aging, Same-day resolution rate, Reopen rate, Comment velocity, WIP per person, Acceptance Criteria presence, Cross-team collaboration score, Silent issues ratio"

## Clarifications

### Session 2025-11-28

- Q: What weighting should description_quality_score use? → A: Balanced: 40% length (>100 chars=full), 40% AC presence, 20% formatting (headers/lists)
- Q: How should cross_team_score map to author count? → A: Diminishing scale: 1 author=25, 2=50, 3=75, 4=90, 5+=100

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Individual Issue Quality Assessment (Priority: P1)

As a team lead, I want to see individual quality metrics for each exported issue, so I can quickly identify problematic issues and understand where to intervene.

**Why this priority**: This is the foundation for all other analyses. Without issue-level metrics, meaningful aggregations cannot be calculated.

**Independent Test**: Can be tested by exporting a set of issues and verifying that each CSV row contains calculated metrics (cycle time, aging, comments count, description quality score).

**Acceptance Scenarios**:

1. **Given** a resolved issue with creation and resolution dates, **When** I export issues, **Then** the CSV contains the cycle time in days for that issue
2. **Given** an open issue created 30 days ago, **When** I export issues, **Then** the CSV shows aging of 30 days
3. **Given** an issue with 5 comments, **When** I export issues, **Then** the CSV shows 5 in the comments_count field
4. **Given** an issue with 500-character description and acceptance criteria, **When** I export issues, **Then** the description_quality_score field is high (>70)
5. **Given** an issue without description, **When** I export issues, **Then** the description_quality_score field is 0

---

### User Story 2 - Project-Level Aggregated Metrics (Priority: P2)

As a project manager, I want to see aggregated metrics per project, so I can compare quality and performance across different projects.

**Why this priority**: Aggregated metrics enable strategic decisions at portfolio level, but require individual metrics (P1) first.

**Independent Test**: Can be tested by generating a project summary file and verifying it contains aggregated metrics (avg cycle time, bug ratio, resolution rate).

**Acceptance Scenarios**:

1. **Given** a project with 10 resolved issues, **When** I export data, **Then** I get a summary file with the project's average cycle time
2. **Given** a project with 20 issues including 5 Bugs, **When** I export data, **Then** the summary shows 25% bug ratio
3. **Given** a project with 8 same-day resolved issues out of 10 total resolved, **When** I export data, **Then** the same-day resolution rate is 80%

---

### User Story 3 - Team Member Performance Metrics (Priority: P2)

As a team lead, I want to see aggregated metrics per person (assignee), so I can understand workload distribution and individual performance.

**Why this priority**: Complementary to P2, enables analysis of work distribution within the team.

**Independent Test**: Can be tested by verifying the person metrics file contains WIP, avg cycle time, and issue count for each assignee.

**Acceptance Scenarios**:

1. **Given** a user with 5 open assigned issues, **When** I export data, **Then** the WIP (Work In Progress) for that person is 5
2. **Given** a user who resolved 10 issues with average time of 3 days, **When** I export data, **Then** their avg cycle time is 3 days
3. **Given** issues assigned to multiple different people, **When** I export data, **Then** each person appears with their own metrics in the file

---

### User Story 4 - Issue Type Performance Analysis (Priority: P3)

As a product owner, I want to see aggregated metrics per issue type (Bug, Story, Task), so I can understand where the team spends most time.

**Why this priority**: Complementary analysis that helps optimize processes by work type.

**Independent Test**: Can be tested by verifying the type summary contains distinct metrics for Bug, Story, Task, etc.

**Acceptance Scenarios**:

1. **Given** 10 Bugs with 2-day average cycle time and 10 Stories with 5-day average cycle time, **When** I export data, **Then** the summary shows these distinct averages per type
2. **Given** Bugs with variable resolution time, **When** I export data, **Then** I get the average Bug Resolution Time

---

### User Story 5 - Collaboration and Communication Metrics (Priority: P3)

As a team lead, I want metrics on collaboration and communication within issues, so I can identify silos or communication problems.

**Why this priority**: Advanced metrics that require the foundational metrics already implemented.

**Independent Test**: Can be tested by verifying issues show cross-team collaboration score and comment velocity.

**Acceptance Scenarios**:

1. **Given** an issue with comments from 3 different people, **When** I export data, **Then** the cross-team collaboration score is ≥75 (per FR-009 diminishing scale)
2. **Given** an issue created Monday with first comment Wednesday, **When** I export data, **Then** the comment velocity (first comment) is 48 hours
3. **Given** an issue without comments, **When** I export data, **Then** it is marked as "silent issue" (silent_issue = true)

---

### Edge Cases

- What happens when an issue has no assignee? → WIP is not counted for anyone, person metrics ignore the issue
- How are issues with negative cycle time handled (data error)? → System logs a warning and sets cycle_time to null
- What happens if an issue was reopened? → If trackable from history, increments reopen_count
- How is description quality score calculated for ADF format descriptions? → Convert to plain text first, then analyze
- What happens with issues without comments? → comments_count = 0, comment_velocity = null, silent_issue = true
- How is division by zero handled in ratios? → Return 0% or null with appropriate note

## Requirements *(mandatory)*

### Functional Requirements

**Issue-Level Metrics (extension of existing export):**

- **FR-001**: System MUST calculate **cycle_time** (days between created and resolution_date) for each resolved issue
- **FR-002**: System MUST calculate **aging** (days between created and today) for each open issue
- **FR-003**: System MUST count the **comments_count** for each issue
- **FR-004**: System MUST calculate a **description_quality_score** (0-100) using balanced weighting: 40% length (>100 chars = full score), 40% acceptance criteria presence, 20% formatting (headers/lists detected)
- **FR-005**: System MUST identify **acceptance_criteria** presence (boolean) by searching for common patterns (Given/When/Then, AC:, Acceptance Criteria, checkbox lists)
- **FR-006**: System MUST calculate **comment_velocity_hours** (hours from created to first comment) for each issue with comments
- **FR-007**: System MUST mark each issue as **silent_issue** (boolean) if it has no comments
- **FR-008**: System MUST indicate if issue is **same_day_resolution** (boolean) if resolved on the same day as creation
- **FR-009**: System MUST calculate a **cross_team_score** (0-100) using diminishing scale based on distinct comment authors: 1 author=25, 2=50, 3=75, 4=90, 5+=100

**Project-Level Aggregated Metrics:**

- **FR-010**: System MUST generate a **jira_project_metrics.csv** file with aggregated metrics per project
- **FR-011**: Project metrics MUST include: avg_cycle_time, median_cycle_time, bug_count, total_issues, bug_ratio_percent
- **FR-012**: Project metrics MUST include: resolved_count, same_day_resolution_rate_percent
- **FR-013**: Project metrics MUST include: avg_description_quality, silent_issues_ratio_percent
- **FR-014**: Project metrics MUST include: avg_comments_per_issue, avg_comment_velocity_hours

**Person-Level Aggregated Metrics:**

- **FR-015**: System MUST generate a **jira_person_metrics.csv** file with aggregated metrics per assignee
- **FR-016**: Person metrics MUST include: assignee_name, wip_count (open assigned issues)
- **FR-017**: Person metrics MUST include: resolved_count, avg_cycle_time_days
- **FR-018**: Person metrics MUST include: total_assigned, bug_count_assigned

**Type-Level Aggregated Metrics:**

- **FR-019**: System MUST generate a **jira_type_metrics.csv** file with aggregated metrics per issue_type
- **FR-020**: Type metrics MUST include: issue_type, count, resolved_count, avg_cycle_time_days
- **FR-021**: For Bugs specifically, MUST calculate **bug_resolution_time_avg** separately

**Reopen Rate (if trackable):**

- **FR-022**: If transition history is available via API, system MUST calculate **reopen_count** per issue
- **FR-023**: System MUST calculate **reopen_rate_percent** in aggregated metrics (reopened issues / resolved issues * 100)

### Key Entities

- **IssueMetrics**: Extension of issue data with calculated fields (cycle_time, aging, comments_count, description_quality_score, acceptance_criteria_present, comment_velocity_hours, silent_issue, same_day_resolution, cross_team_score, reopen_count)
- **ProjectMetrics**: Aggregation by project_key with averages, medians, ratios and counts
- **PersonMetrics**: Aggregation by assignee with WIP, performance and volumes
- **TypeMetrics**: Aggregation by issue_type with cycle time and volumes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify "silent" issues (without comments) in less than 30 seconds by opening the CSV
- **SC-002**: Users can compare performance across 5+ projects in a single view (summary file)
- **SC-003**: Average cycle time is calculated with day precision for 100% of resolved issues
- **SC-004**: Description quality score identifies at least 80% of issues with insufficient description (< 50 characters or no AC)
- **SC-005**: Export generation time with metrics does not exceed 200% of current base export time
- **SC-006**: Users can see each team member's WIP to plan work allocation

## Assumptions

- Comments are already retrieved by the existing system (JiraClient.get_comments already implemented)
- Creation and resolution dates are always present and valid for resolved issues
- Acceptance criteria identification is based on common text patterns (Given/When/Then, checkbox markdown, keyword "Acceptance Criteria")
- Cross-team score is based on comment author diversity, not an explicit team field
- Transition history for reopen rate may not be available in all Jira configurations (FR-022/FR-023 are best-effort)
- Description quality score is a simple heuristic, not advanced semantic analysis
