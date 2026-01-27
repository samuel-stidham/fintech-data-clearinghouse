import time
import os
import paramiko
import pandas as pd
import threading
from io import StringIO
from . import db
from .models import Trade, ComplianceAlert


class SftpIngestionService:
    def __init__(self, app):
        self.app = app
        self.host = os.getenv("SFTP_HOST", "sftp")
        self.port = int(os.getenv("SFTP_PORT", 22))
        self.user = os.getenv("SFTP_USER", "vest_user")
        self.password = os.getenv("SFTP_PASS", "pass")
        self.input_dir = os.getenv("SFTP_INPUT_DIR", "/upload")
        self.processed_dir = os.getenv("SFTP_PROCESSED_DIR", "/upload/processed")

    def get_transport(self):
        try:
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.user, password=self.password)
            return transport
        except Exception as e:
            print(f"[SFTP] Connection failed: {e}")
            return None

    def check_compliance(self, trade_data):
        """
        Compliance Logic:
        We flag any trade with a quantity > 100.

        TRADEOFF NOTE:
        Ideally, we would check for "Portfolio Concentration" (e.g., no single position
        > 20% of total portfolio value). However, the input CSVs only contain isolated
        trade lists, not the client's total holdings or net worth.

        Without access to the 'Total Portfolio Value', we cannot calculate a true
        concentration percentage. Therefore, we use a hardcoded "Large Order" cap
        of 100 shares as a proxy for risk.
        """
        alerts = []
        qty = abs(trade_data["quantity"])

        if qty > 100:
            alerts.append(
                {
                    "rule": "High Volume (>100)",
                    "severity": "WARNING",
                    "description": f"Trade quantity {qty} exceeds threshold of 100.",
                }
            )

        return alerts

    def normalize_data(self, content, filename):
        """
        Detects format and returns a standardized DataFrame.
        Format 1: CSV (TradeDate, AccountID...)
        Format 2: Pipe (REPORT_DATE|ACCOUNT_ID...)
        """
        try:
            if "|" in content.splitlines()[0]:
                print(f"[SFTP] Detected Format 2 (Pipe) for {filename}")
                df = pd.read_csv(StringIO(content), sep="|")

                normalized = pd.DataFrame()
                normalized["date"] = pd.to_datetime(
                    df["REPORT_DATE"].astype(str), format="%Y%m%d"
                ).dt.date
                normalized["account"] = df["ACCOUNT_ID"]
                normalized["ticker"] = df["SECURITY_TICKER"]
                normalized["quantity"] = df["SHARES"]
                normalized["price"] = (df["MARKET_VALUE"] / df["SHARES"]).abs()

                return normalized

            else:
                print(f"[SFTP] Detected Format 1 (CSV) for {filename}")
                df = pd.read_csv(StringIO(content))

                normalized = pd.DataFrame()
                normalized["date"] = pd.to_datetime(df["TradeDate"]).dt.date
                normalized["account"] = df["AccountID"]
                normalized["ticker"] = df["Ticker"]
                normalized["quantity"] = df["Quantity"]
                normalized["price"] = df["Price"]

                return normalized

        except Exception as e:
            print(f"[SFTP] Normalization Error in {filename}: {e}")
            return None

    def process_file(self, filename, sftp):
        print(f"[SFTP] Processing {filename}...")
        full_path = f"{self.input_dir}/{filename}"

        try:
            with sftp.open(full_path, "r") as remote_file:
                content = remote_file.read().decode("utf-8")

            # 1. Normalize Data
            df = self.normalize_data(content, filename)
            if df is None or df.empty:
                print(f"[SFTP] Skipping {filename}: No valid data found.")
                return False

            # 2. Ingest Transactionally
            with self.app.app_context():
                for _, row in df.iterrows():
                    new_trade = Trade(
                        trade_date=row["date"],
                        account=row["account"],
                        ticker=row["ticker"],
                        quantity=int(row["quantity"]),
                        price=float(row["price"]),
                    )
                    db.session.add(new_trade)
                    db.session.flush()

                    # Compliance Check (Uses the 100 share cap logic)
                    violations = self.check_compliance(row)

                    for v in violations:
                        alert = ComplianceAlert(
                            trade_id=new_trade.id,
                            rule_name=v["rule"],
                            severity=v["severity"],
                            description=v["description"],
                        )
                        db.session.add(alert)
                        print(f"   [!] ALERT: {row['ticker']} - {v['rule']}")

                db.session.commit()
                print(f"[SFTP] Success: Ingested {len(df)} trades from {filename}")

            return True

        except Exception as e:
            print(f"[SFTP] Error processing {filename}: {e}")
            return False

    def run_cycle(self):
        transport = self.get_transport()
        if not transport:
            return

        try:
            sftp = paramiko.SFTPClient.from_transport(transport)

            try:
                sftp.mkdir(self.processed_dir)
            except IOError:
                pass

            files = sftp.listdir(self.input_dir)

            for file in files:
                if file == "processed":
                    continue

                if (
                    file.endswith(".csv")
                    or file.endswith(".txt")
                    or file.endswith(".dat")
                ):
                    if self.process_file(file, sftp):
                        old_path = f"{self.input_dir}/{file}"
                        new_path = f"{self.processed_dir}/{file}"
                        try:
                            try:
                                sftp.remove(new_path)
                            except IOError:
                                pass

                            sftp.rename(old_path, new_path)
                            print(f"[SFTP] Archived {file} to {new_path}")
                        except IOError as e:
                            print(f"[SFTP] CRITICAL: Failed to move {file}: {e}")

        except Exception as e:
            print(f"[SFTP] Cycle error: {e}")
        finally:
            if transport:
                transport.close()

    def start_background_loop(self):
        def loop():
            print("[SFTP] Watcher started. Waiting for files...")
            while True:
                self.run_cycle()
                time.sleep(10)

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        print("[SFTP] Background ingestion service started.")
