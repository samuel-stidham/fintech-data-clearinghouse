# Architectural Trade-offs & Decisions

**Context:** This project was executed within a strictly time-boxed window (4-6 hours).
The following document outlines where "Production Best Practices" were intentionally exchanged for "Development Speed" and "Simplicity" to ensure a functional deliverable within the deadline.

---

## 1. Dependency Management: `requirements.txt` vs. Poetry

### Decision

I chose a pinned `requirements.txt` file over a modern tool like Poetry.

### Trade-off Analysis

- **The "Right" Way (Poetry):** In a long-term production environment, I prefer Poetry for its deterministic dependency resolution, lockfile integrity, and virtualenv management.
- **The Pragmatic Choice (`requirements.txt`):** Poetry introduces setup overhead (installing the binary in CI/Docker) and complexity (multi-stage builds to handle venvs).
- **Impact:** By using `requirements.txt`, I optimized for **Docker build speed** and **CI simplicity**. The risk of "works on my machine" issues is mitigated by pinning versions and exclusively running the app in containers.

---

## 2. Infrastructure: Single Node vs. Distributed

### Decision

Deployed a single EC2 instance (`t3.medium`) running the entire stack via Docker Compose (Flask App + Postgres + SFTP).

### Trade-off Analysis

- **The "Right" Way (Cloud Native):** A robust architecture would decouple these services:
  - **App:** AWS ECS (Fargate) or EKS for auto-scaling and zero-downtime deployments.
  - **Database:** Amazon RDS (Multi-AZ) for managed backups and durability.
  - **Ingestion:** AWS Transfer Family backed by S3 for a managed SFTP experience.
- **The Pragmatic Choice (Monolith):**
  - **IAM Complexity:** AWS Transfer Family requires complex IAM roles that risk hitting the assessment environment's Permission Boundaries.
  - **Provisioning Time:** RDS instances take 10-15 minutes to provision. A Docker container is instant.
- **Impact:** This decision reduced Terraform complexity by ~70% and deployment time to under 2 minutes, allowing more time to focus on Python logic and compliance rules.

---

## 3. Terraform State: S3 Backend (No Locking)

### Decision

Used an S3 backend for state storage but omitted the DynamoDB locking table.

### Trade-off Analysis

- **The "Right" Way:** Production Terraform requires a DynamoDB table to lock the state file, preventing two engineers from applying changes simultaneously and corrupting the infrastructure.
- **The Pragmatic Choice:** As the sole engineer working on this assessment, the probability of a race condition is zero.
- **Impact:** Saved time on bootstrapping infrastructure code.

---

## 4. Ingestion Strategy: Synchronous GET vs. Async Worker

### Decision

Ingestion is triggered via a `GET /ingest` endpoint rather than a detached background worker or a semantic `POST` request.

### Trade-off Analysis

- **The "Right" Way:** Heavy ETL jobs should be offloaded to a task queue (e.g., Celery/Redis) to prevent blocking the web server. Semantically, triggering a data change should use the `POST` verb.
- **The Pragmatic Choice:**
  - **Queue:** Implementing a worker tier requires an additional service (Redis) and complex observability.
  - **HTTP Verb:** Using `GET` allows the ingestion to be triggered easily from a browser address bar or a simple liveness probe, simplifying the "Smoketest" requirement.
- **Impact:** The system is easier to test and observe within the scope of this exercise, though it breaks HTTP semantics (GET should be idempotent/safe).

---

## 5. Security: Environment Variables vs. Secrets Manager

### Decision

Secrets (DB passwords, API keys) are injected via GitHub Actions Secrets into container Environment Variables.

### Trade-off Analysis

- **The "Right" Way:** Secrets should be fetched at runtime from AWS Secrets Manager or Systems Manager Parameter Store to avoid exposing them in the container environment or process list.
- **The Pragmatic Choice:** Environment variables are the standard 12-Factor App approach and are sufficient for a private assessment environment.
