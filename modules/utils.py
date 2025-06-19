import datetime
import json
import random
import string
from email.mime.text import MIMEText
import csv
import io
from django.core.validators import RegexValidator
import pytz

alphanumeric = RegexValidator(
    r"^[0-9a-zA-Z\-_ ]*$", "Only alphanumeric characters are allowed."
)


def load_json(filename):
    """Load JSON data from a file."""
    with open(filename, 'r') as file:
        return json.load(file)


def generate_gateway_order_id(suffix="D"):
    # suffix can be C (Credit) or D (Debit)
    """
    Total combinations = 36^8 = 2,821,109,907,456

    Assuming a perfect random distribution and no collisions, each generated unique_str would be unique among the 2,821,109,907,456 possible combinations.
    However, in practice, collisions can occur due to factors such as limited entropy and the birthday paradox. The birthday paradox states that the probability of two or more items colliding increases as the number of items (generated unique_strs) increases.
    To estimate the collision rate, we can use the birthday paradox formula:

    P(collision) ≈ 1 - exp(-n^2 / (2 * d))
    where:
    P(collision) is the probability of a collision
    n is the number of unique_strs generated
    d is the total number of possible combinations (2,821,109,907,456)
    Let's calculate the collision rate for different values of n:

    For n = 1,000,000: P(collision) ≈ 0.0000354% (very low probability)
    For n = 10,000,000: P(collision) ≈ 0.354% (low probability)
    For n = 100,000,000: P(collision) ≈ 35.4% (significant probability)
    """
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    year = str(now.year)[-2:]  # Last two digits of the year
    month = str(now.month).zfill(2)  # Month with leading zero if necessary
    day = str(now.day).zfill(2)  # Day with leading zero if necessary
    hour = str(now.hour).zfill(2)  # Hour with leading zero if necessary
    minute = str(now.minute).zfill(2)  # Minute with leading zero if necessary
    second = str(now.second).zfill(2)  # Minute with leading zero if necessary

    # Generate unique 6-digit alphanumeric string
    unique_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    unique_id = f"{year}{month}{day}{hour}{minute}{second}{unique_str}{suffix}"
    return unique_id


def test_pnr_generator(num_iterations):
    # Generate a PNR in the format YYMMDDHHMM<6-digit-unique-capital-str>
    pnr = generate_gateway_order_id()
    print(pnr)

    pnr_set = set()
    collisions = 0

    for _ in range(num_iterations):
        pnr = generate_gateway_order_id()
        if pnr in pnr_set:
            collisions += 1
        else:
            pnr_set.add(pnr)

    collision_percentage = (collisions / num_iterations) * 100
    print(f"Collisions: {collisions}/{num_iterations}; {collision_percentage}%")
    return collision_percentage


def convert_data_to_csv_string(data):
    csv_string = ','.join(data[0].keys()) + '\n'  # headers
    for row in data:
        csv_string += ','.join(row.values()) + '\n'
    return csv_string


def generate_random_csv_attachments(number_of_files, rows, columns):
    attachments = {}
    for _ in range(number_of_files):
        filename = f"test_{random.randint(1, 1000)}.csv"
        data = generate_random_csv_data(rows, columns)
        attachment = MIMEText(convert_data_to_csv_string(data), 'plain')
        attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        attachments[filename] = attachment
    return attachments


def generate_random_csv_data(rows, columns):
    data = []
    headers = ['Column_' + str(i) for i in range(columns)]
    for _ in range(rows):
        row = {header: ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) for header in headers}
        data.append(row)
    return data


def convert_objects_to_csv(data, headers):
    """
    Convert a list of dictionaries to a CSV string.
    Use provided headers, and include them even if there is no data.

    :param data: List of dictionaries
    :param headers: List of header strings
    :return: CSV string
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)

    writer.writeheader()
    for row in data:
        writer.writerow(row)

    return output.getvalue()


def save_csv_file(filename, csv_string):
    """
    Save the CSV string to a file.

    :param filename: The name of the file where the CSV data should be saved
    :param csv_string: The CSV data as a string
    """
    with open(filename, 'w', newline='') as file:
        file.write(csv_string)


if __name__ == "__main__":
    # Test the PNR generator iterations and report collision percentage
    # iterations = 500000
    # test_pnr_generator(iterations)
    pass
