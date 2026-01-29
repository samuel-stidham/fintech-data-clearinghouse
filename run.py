from app import create_app
from app.migrate import run_migrations

# First, run migrations to ensure the database is set up
run_migrations()

app = create_app()

if __name__ == "__main__":
    # Start the SFTP Ingestion Service exactly once
    from app.ingest import SftpIngestionService

    ingestor = SftpIngestionService(app)
    ingestor.start_background_loop()

    # Run the app
    app.run(host="0.0.0.0", port=5000)
