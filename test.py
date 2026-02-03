import csv

input_file = "results (2).csv"
output_file = "results (2)_unlimited.csv"

with open(input_file, newline="", encoding="utf-8") as infile, \
     open(output_file, "w", newline="", encoding="utf-8") as outfile:

    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)

    writer.writeheader()

    for row in reader:
        if row["Condition"]:
            row["Condition"] = f'{row["Condition"]} Unlimited'
        else:
            row["Condition"] = "Unlimited"

        writer.writerow(row)

print("Done! Updated file saved as:", output_file)