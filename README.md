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

This dataset was created to test mixed Buy/Sell orders, different tickers, and various trade values to ensure the **20% basket concentration rule** triggered correctly.

Input (`test_data.csv`):

```csv
TradeDate,AccountID,Ticker,Quantity,Price,TradeType,SettlementDate
2025-01-15,ACC001,AAPL,100,185.50,BUY,2025-01-17
2025-01-15,ACC001,MSFT,50,420.25,BUY,2025-01-17
2025-01-15,ACC002,GOOGL,75,142.80,BUY,2025-01-17
2025-01-15,ACC002,AAPL,200,185.50,BUY,2025-01-17
2025-01-15,ACC003,TSLA,150,238.45,SELL,2025-01-17
2025-01-15,ACC003,NVDA,80,505.30,BUY,2025-01-17
2025-01-15,ACC001,GOOGL,100,142.80,BUY,2025-01-17
2025-01-15,ACC004,AAPL,500,185.50,BUY,2025-01-17
2025-01-15,ACC004,MSFT,300,420.25,BUY,2025-01-17
2025-01-15,ACC002,NVDA,120,505.30,BUY,2025-01-17
```

System Output:

```text
web-1   | [SFTP] Processing test_data.csv...
web-1   | [SFTP] Detected Format 1 (CSV) for test_data.csv
web-1   |    [!] ALERT: ACC001 / AAPL is 34.5% of basket.
web-1   |    [!] ALERT: ACC001 / MSFT is 39.0% of basket.
web-1   |    [!] ALERT: ACC002 / AAPL is 34.2% of basket.
web-1   |    [!] ALERT: ACC003 / TSLA is 46.9% of basket.
web-1   |    [!] ALERT: ACC003 / NVDA is 53.1% of basket.
web-1   |    [!] ALERT: ACC001 / GOOGL is 26.5% of basket.
web-1   |    [!] ALERT: ACC004 / AAPL is 42.4% of basket.
web-1   |    [!] ALERT: ACC004 / MSFT is 57.6% of basket.
web-1   |    [!] ALERT: ACC002 / NVDA is 55.9% of basket.
web-1   | [SFTP] Success: Ingested 10 trades from test_data.csv
```

### 2. Standard Formats (Requirements Data)

The system successfully auto-detected and processed both the Comma-Separated (Format 1) and Pipe-Separated (Format 2) files provided in the prompt.

Format 1 Output (`test_file1.csv`):

```text
web-1   | [SFTP] Processing test_file1.csv...
web-1   | [SFTP] Detected Format 1 (CSV) for test_file1.csv
web-1   |    [!] ALERT: ACC001 / AAPL is 34.5% of basket.
web-1   |    [!] ALERT: ACC001 / MSFT is 39.0% of basket.
web-1   |    [!] ALERT: ACC002 / AAPL is 34.2% of basket.
web-1   |    [!] ALERT: ACC003 / TSLA is 46.9% of basket.
web-1   |    [!] ALERT: ACC003 / NVDA is 53.1% of basket.
web-1   |    [!] ALERT: ACC001 / GOOGL is 26.5% of basket.
web-1   |    [!] ALERT: ACC004 / AAPL is 42.4% of basket.
web-1   |    [!] ALERT: ACC004 / MSFT is 57.6% of basket.
web-1   |    [!] ALERT: ACC002 / NVDA is 55.9% of basket.
web-1   | [SFTP] Success: Ingested 10 trades from test_file1.csv
web-1   | [SFTP] Archived test_file1.csv to /upload/processed/test_file1.csv
```

Format 2 Output (`test_file2.csv`):

```text
web-1   | [SFTP] Processing test_file2.csv...
web-1   | [SFTP] Detected Format 2 (Pipe) for test_file2.csv
web-1   |    [!] ALERT: ACC001 / AAPL is 34.5% of basket.
web-1   |    [!] ALERT: ACC001 / MSFT is 39.0% of basket.
web-1   |    [!] ALERT: ACC001 / GOOGL is 26.5% of basket.
web-1   |    [!] ALERT: ACC002 / AAPL is 34.2% of basket.
web-1   |    [!] ALERT: ACC002 / NVDA is 55.9% of basket.
web-1   |    [!] ALERT: ACC003 / TSLA is 46.9% of basket.
web-1   |    [!] ALERT: ACC003 / NVDA is 53.1% of basket.
web-1   |    [!] ALERT: ACC004 / AAPL is 42.4% of basket.
web-1   |    [!] ALERT: ACC004 / MSFT is 57.6% of basket.
web-1   | [SFTP] Success: Ingested 10 trades from test_file2.csv
web-1   | [SFTP] Archived test_file2.csv to /upload/processed/test_file2.csv
```

## API Endpoints Demo

Below are the actual responses from the service after ingesting the sample data for **2025-01-15**.

### 1. Daily Blotter
**Endpoint:** `GET /blotter?date=2025-01-15`
Returns a simplified view of all raw trades for the specified date.

```json
[{"account":"ACC001","id":1,"price":185.5,"quantity":100,"ticker":"AAPL","total_value":18550.0},{"account":"ACC001","id":2,"price":420.25,"quantity":50,"ticker":"MSFT","total_value":21012.5},{"account":"ACC002","id":3,"price":142.8,"quantity":75,"ticker":"GOOGL","total_value":10710.0},{"account":"ACC002","id":4,"price":185.5,"quantity":200,"ticker":"AAPL","total_value":37100.0},{"account":"ACC003","id":5,"price":238.45,"quantity":150,"ticker":"TSLA","total_value":35767.5},{"account":"ACC003","id":6,"price":505.3,"quantity":80,"ticker":"NVDA","total_value":40424.0},{"account":"ACC001","id":7,"price":142.8,"quantity":100,"ticker":"GOOGL","total_value":14280.000000000002},{"account":"ACC004","id":8,"price":185.5,"quantity":500,"ticker":"AAPL","total_value":92750.0},{"account":"ACC004","id":9,"price":420.25,"quantity":300,"ticker":"MSFT","total_value":126075.0},{"account":"ACC002","id":10,"price":505.3,"quantity":120,"ticker":"NVDA","total_value":60636.0}]
```

### 2. Account Positions
**Endpoint:** `GET /positions?date=2025-01-15`
Aggregates trades to show the percentage allocation of each asset per account.

```json
{"ACC001":{"AAPL":"34.5%","GOOGL":"26.5%","MSFT":"39.0%"},"ACC002":{"AAPL":"34.2%","GOOGL":"9.9%","NVDA":"55.9%"},"ACC003":{"NVDA":"53.1%","TSLA":"46.9%"},"ACC004":{"AAPL":"42.4%","MSFT":"57.6%"}}
```

### 3. Compliance Alarms
**Endpoint:** `GET /alarms?date=2025-01-15`
Identifies any account where a single ticker constitutes >20% of the daily trading volume.

```json
[{"account":"ACC001","description":"Ticker AAPL represents 34.5% of Account ACC001's batch order.","rule":"Basket Concentration (>20%)","ticker":"AAPL","triggered":true},{"account":"ACC001","description":"Ticker MSFT represents 39.0% of Account ACC001's batch order.","rule":"Basket Concentration (>20%)","ticker":"MSFT","triggered":true},{"account":"ACC002","description":"Ticker AAPL represents 34.2% of Account ACC002's batch order.","rule":"Basket Concentration (>20%)","ticker":"AAPL","triggered":true},{"account":"ACC003","description":"Ticker TSLA represents 46.9% of Account ACC003's batch order.","rule":"Basket Concentration (>20%)","ticker":"TSLA","triggered":true},{"account":"ACC003","description":"Ticker NVDA represents 53.1% of Account ACC003's batch order.","rule":"Basket Concentration (>20%)","ticker":"NVDA","triggered":true},{"account":"ACC001","description":"Ticker GOOGL represents 26.5% of Account ACC001's batch order.","rule":"Basket Concentration (>20%)","ticker":"GOOGL","triggered":true},{"account":"ACC004","description":"Ticker AAPL represents 42.4% of Account ACC004's batch order.","rule":"Basket Concentration (>20%)","ticker":"AAPL","triggered":true},{"account":"ACC004","description":"Ticker MSFT represents 57.6% of Account ACC004's batch order.","rule":"Basket Concentration (>20%)","ticker":"MSFT","triggered":true},{"account":"ACC002","description":"Ticker NVDA represents 55.9% of Account ACC002's batch order.","rule":"Basket Concentration (>20%)","ticker":"NVDA","triggered":true}]
```

## Full Disclosure

This project was completed with assistance from **GitHub Copilot** (coding speed/autocomplete) and **Google Gemini** (architectural planning and trade-off analysis).
