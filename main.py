import argparse
import sys

from config import load_config
from logger import setup_logger
from scheduler import check_and_reply, run_scheduler
from ai_client import create_client
from tracker import ReplyTracker


def main():
    parser = argparse.ArgumentParser(
        description="AI Pen Pal - Automatic email reply bot with AI character"
    )
    parser.add_argument(
        "--config", "-c",
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one check cycle and exit (for testing)",
    )
    parser.add_argument(
        "--gui", "-g",
        action="store_true",
        help="Launch GUI mode",
    )
    args = parser.parse_args()

    if args.gui or (getattr(sys, 'frozen', False) and not args.once):
        from gui.app import main as gui_main
        gui_main()
        return

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Hint: Copy config.example.yaml to config.yaml and fill in your settings.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    logger = setup_logger(config.logging.level, config.logging.file)

    if args.once:
        logger.info("Running single check cycle (--once mode)")
        tracker = ReplyTracker(config.tracking.db_path)
        ai_client = create_client(
            provider=config.model.provider,
            api_key=config.model.api_key,
            model_name=config.model.model_name,
            base_url=config.model.base_url,
            max_tokens=config.model.max_tokens,
            temperature=config.model.temperature,
        )
        check_and_reply(config, ai_client, tracker)
        tracker.close()
        logger.info("Single check cycle complete.")
    else:
        run_scheduler(config)


if __name__ == "__main__":
    main()
