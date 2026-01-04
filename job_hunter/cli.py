import argparse
from job_hunter.pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(
        description="Job Hunter – AI-ready job crawler & matcher"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="CSV file with company and career_url"
    )

    parser.add_argument(
        "--output",
        default="jobs.csv",
        help="Output CSV file"
    )

    args = parser.parse_args()

    run_pipeline(
        input_file=args.input,
        output_file=args.output
    )

if __name__ == "__main__":
    main()
