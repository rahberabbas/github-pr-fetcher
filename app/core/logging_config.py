import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Output logs to console
        logging.FileHandler("app.log")  # Also save logs to a file
    ]
)

logger = logging.getLogger(__name__)
