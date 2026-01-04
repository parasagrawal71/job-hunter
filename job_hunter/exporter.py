import csv
from job_hunter.constants import CompanyWithZeroLinksCSVField


def export_companies_with_zero_links(dataList, output_file):
    fieldnames = list(CompanyWithZeroLinksCSVField)

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for index, data in enumerate(dataList, start=1):
            writer.writerow(
                {
                    CompanyWithZeroLinksCSVField.S_NO.value: index,
                    CompanyWithZeroLinksCSVField.COMPANY.value: data["company"],
                    CompanyWithZeroLinksCSVField.CAREER_URL.value: data["career_url"],
                }
            )
