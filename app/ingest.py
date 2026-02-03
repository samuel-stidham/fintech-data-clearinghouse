import time
import os
import paramiko
import pandas as pd
import threading
from io import StringIO
from sqlalchemy.dialects.postgresql import insert as pg_insert
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

    def normalize_data(self, content, filename):
        """
        Detects format and returns a standardized DataFrame.
        Standardized Columns: date, account, ticker, quantity, price
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

            df = self.normalize_data(content, filename)
            if df is None or df.empty:
                print(f"[SFTP] Skipping {filename}: No valid data found.")
                return False

            df["row_value"] = df["quantity"].abs() * df["price"]
            account_totals = df.groupby("account")["row_value"].sum().to_dict()

            with self.app.app_context():
                for _, row in df.iterrows():
                    stmt = pg_insert(Trade).values(
                        trade_date=row["date"],
                        account=row["account"],
                        ticker=row["ticker"],
                        quantity=int(row["quantity"]),
                        price=float(row["price"]),
                    )

                    upsert_stmt = stmt.on_conflict_do_update(
                        constraint="_account_ticker_date_uc",
                        set_={
                            "quantity": stmt.excluded.quantity,
                            "price": stmt.excluded.price,
                        },
                    ).returning(Trade)

                    result = db.session.execute(upsert_stmt)
                    current_trade = result.scalar_one()

                    account_total = account_totals.get(row["account"], 0)
                    row_val = row["row_value"]

                    concentration = 0
                    if account_total > 0:
                        concentration = row_val / account_total

                    if concentration > 0.20:
                        pct_str = f"{concentration:.1%}"
                        rule_name = "Basket Concentration (>20%)"

                        existing_alert = ComplianceAlert.query.filter_by(
                            trade_id=current_trade.id, rule_name=rule_name
                        ).first()

                        if not existing_alert:
                            alert = ComplianceAlert(
                                trade_id=current_trade.id,
                                rule_name=rule_name,
                                severity="WARNING",
                                description=f"Ticker {row['ticker']} represents {pct_str} of Account {row['account']}'s batch order.",
                            )
                            db.session.add(alert)
                            print(
                                f"   [!] ALERT: {row['account']} / {row['ticker']} is {pct_str} of basket."
                            )

                db.session.commit()
                print(f"[SFTP] Success: Ingested {len(df)} trades from {filename}")

            return True

        except Exception as e:
            print(f"[SFTP] Error processing {filename}: {e}")
            db.session.rollback()
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

                if file.endswith(".csv"):
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
