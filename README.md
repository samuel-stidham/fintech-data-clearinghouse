# Fintech Data Clearinghouse

**Status:** Technical Assessment Submission

**Candidate:** Samuel Stidham

**Date:** January 26-27 2026

---

## ⚠️ Assessment Submission

This repository contains the code for a technical assessment.

**Please Note:** This is a personal submission. Issues and Pull Requests will not be accepted or reviewed unless they are made by the reviewer of this submission.

---

## Prerequisites

1. Install the [AWS cli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. Install the [Terraform cli](https://developer.hashicorp.com/terraform/install)

---

## Project - Portfolio Data Clearinghouse

We are creating a very simplified version of a data clearinghouse. Each day, possibly several times a day, files are dropped to an FTP server. The files have to be ingested into a relational database, and an API sits in front of the database that allows us to access various kinds of data about our accounts.

We’re particularly interested in a specific compliance rule that does not allow any holding to be over **20%** of the account.

### Key Deliverables

1.  **Robust unit testing**
2.  **Working code**
3.  **CICD pipeline**
4.  **Observability**
5.  **Very basic alerting**

## Functional Requirements

For this exercise, we deployed a service via GitHub Actions that performs the following:

1.  **Ingestion Service:**
    - Ingests files of two different formats (Transactional CSV and Pipe-delimited Snapshot) into a single relational database table.
    - Triggered via an HTTP request or Cron.

2.  **Business API (3 Endpoints):**
    - `GET /blotter?date=<YYYY-MM-DD>`: Returns report data in a simplified format.
    - `GET /positions?date=<YYYY-MM-DD>`: Returns the percentage of funds by ticker for each account.
    - `GET /alarms?date=<YYYY-MM-DD>`: Returns `true` for any account with >20% of any ticker.

3.  **Observability & Liveness:**
    - **Deviation:** While the requirements requested a smoketest for the business endpoints, we implemented a dedicated **`GET /health`** endpoint.
    - **Reasoning:** This adheres to industry standards for liveness probes (e.g., AWS Load Balancers, Kubernetes) and separates operational monitoring from business logic parameters.
    - **Deep Check:** This endpoint does not just return static JSON. It actively attempts a query (`SELECT 1`) against the database to ensure full connectivity before reporting "Healthy."
    - **Smoketest:** A script in the CI pipeline pings this endpoint to verify deployment success.

4.  **CICD:** A pipeline using GitHub Actions and Terraform.

5.  **Security:** Preshared API Key authentication.

6.  **Alerting:** A mocked service that logs alerts for system failures and compliance breaches.

---

## Architecture & Trade-offs

Given the **4-6 hour constraint** for this exercise, specific architectural trade-offs were made to balance "Working Code" with "Production Best Practices."

Decisions regarding **Dependency Management** (Poetry vs requirements.txt), **Infrastructure** (EC2 vs ECS), and **State Management** are detailed in the [TRADEOFFS.md](TRADEOFFS.md) file.

---

## Quick Start (Local)

You can run the entire stack (Database, App, and Mock SFTP) locally using Docker Compose.

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/samuel-stidham/fintech-data-clearinghouse.git](https://github.com/samuel-stidham/fintech-data-clearinghouse.git)
    cd fintech-data-clearinghouse
    ```

2.  **Run the Stack:**

    ```bash
    docker-compose up --build
    ```

3.  **Test Endpoints:**
    - **Health Check (Operational):**
      `curl localhost:5000/health`
      _Expected Response:_ `{"status": "OK", "database": "connected"}`
    - **Blotter (Business):**
      `curl "localhost:5000/blotter?date=2025-01-15"`
    - **Positions (Business):**
      `curl "localhost:5000/positions?date=2025-01-15"`
    - **Alarms (Business/Compliance):**
      `curl "localhost:5000/alarms?date=2025-01-15"`

    _> **Note on Ingestion:** The application includes a background poller that automatically detects, ingests, and archives files dropped into the SFTP folder every 10 seconds. No manual trigger is required._

---

## Deployment (AWS)

Deployment is handled via GitHub Actions using the `deployer` SSH key.

1.  **Infrastructure Provisioning:**
    ```bash
    cd build/terraform
    terraform init
    terraform apply
    ```
2.  **Pipeline:**
    Pushing to the `main` branch triggers the workflow defined in `.github/workflows/deploy.yml`.

## Test Data Validation

To validate the ingestion pipeline, I ran three test scenarios: a custom dataset designed to target specific edge cases, and the two required formats provided in the requirements.

### 1. Custom Dataset

This dataset was created to test mixed Buy/Sell orders, different tickers, and various quantity thresholds to ensure the 100-share limit triggered correctly.

Input (test_data.csv):

```csv
TradeDate,AccountID,Ticker,Quantity,Price,TradeType,SettlementDate
2025-01-15,ACC001,AAPL,150,185.50,BUY,2025-01-17
2025-01-15,ACC001,MSFT,50,420.25,BUY,2025-01-17
2025-01-15,ACC002,GOOGL,75,142.80,BUY,2025-01-17
2025-01-15,ACC002,TSLA,200,210.00,SELL,2025-01-17
2025-01-15,ACC003,NVDA,80,505.30,BUY,2025-01-17
2025-01-15,ACC003,AMZN,500,155.00,BUY,2025-01-17
2025-01-15,ACC004,META,25,360.00,SELL,2025-01-17
2025-01-15,ACC004,NFLX,120,490.00,BUY,2025-01-17
```

System Output:

```text
web-1   | [SFTP] Processing test_data.csv...
web-1   | [SFTP] Detected Format 1 (CSV) for test_data.csv
web-1   |    [!] ALERT: AAPL - High Volume (>100)
web-1   |    [!] ALERT: TSLA - High Volume (>100)
web-1   |    [!] ALERT: AMZN - High Volume (>100)
web-1   |    [!] ALERT: NFLX - High Volume (>100)
web-1   | [SFTP] Success: Ingested 8 trades from test_data.csv
web-1   | [SFTP] Archived test_data.csv to /upload/processed/test_data.csv
```

### 2. Standard Formats (Requirements Data)

The system successfully auto-detected and processed both the Comma-Separated (Format 1) and Pipe-Separated (Format 2) files provided in the prompt.

Format 1 Output (test_file1.csv):

```text
web-1   | [SFTP] Processing test_file1.csv...
web-1   | [SFTP] Detected Format 1 (CSV) for test_file1.csv
web-1   |    [!] ALERT: AAPL - High Volume (>100)
web-1   |    [!] ALERT: TSLA - High Volume (>100)
web-1   |    [!] ALERT: AAPL - High Volume (>100)
web-1   |    [!] ALERT: MSFT - High Volume (>100)
web-1   |    [!] ALERT: NVDA - High Volume (>100)
web-1   | [SFTP] Success: Ingested 10 trades from test_file1.csv
web-1   | [SFTP] Archived test_file1.csv to /upload/processed/test_file1.csv
```

Format 2 Output (test_file2.csv):

```text
web-1   | [SFTP] Processing test_file2.csv...
web-1   | [SFTP] Detected Format 2 (Pipe) for test_file2.csv
web-1   |    [!] ALERT: AAPL - High Volume (>100)
web-1   |    [!] ALERT: NVDA - High Volume (>100)
web-1   |    [!] ALERT: TSLA - High Volume (>100)
web-1   |    [!] ALERT: AAPL - High Volume (>100)
web-1   |    [!] ALERT: MSFT - High Volume (>100)
web-1   | [SFTP] Success: Ingested 10 trades from test_file2.csv
web-1   | [SFTP] Archived test_file2.csv to /upload/processed/test_file2.csv
```

## Full Disclosure

This project was completed with assistance from **GitHub Copilot** (coding speed/autocomplete) and **Google Gemini** (architectural planning and trade-off analysis).
