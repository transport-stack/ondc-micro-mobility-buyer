import datetime
import random
import string

import pytz


def generate_pnr():
    """
    Collisions: 59/500000; 0.0118%
    This ran in under 1 minute on my machine.
    Means, if there are 500k PNRs for the whole day, there won't be any collision as the HHMM part will also vary
    """
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    year = str(now.year)[-2:]  # Last two digits of the year
    month = str(now.month).zfill(2)  # Month with leading zero if necessary
    day = str(now.day).zfill(2)  # Day with leading zero if necessary
    hour = str(now.hour).zfill(2)  # Hour with leading zero if necessary
    minute = str(now.minute).zfill(2)  # Minute with leading zero if necessary

    # Generate unique 6-digit alphanumeric string
    unique_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    pnr = f"{year}{month}{day}{hour}{minute}{unique_str}"
    return pnr


def test_pnr_generator(num_iterations):
    # Generate a PNR in the format YYMMDDHHMM<6-digit-unique-capital-str>
    pnr = generate_pnr()
    print(pnr)

    pnr_set = set()
    collisions = 0

    for _ in range(num_iterations):
        pnr = generate_pnr()
        if pnr in pnr_set:
            collisions += 1
        else:
            pnr_set.add(pnr)

    collision_percentage = (collisions / num_iterations) * 100
    print(f"Collisions: {collisions}/{num_iterations}; {collision_percentage}%")
    return collision_percentage


if __name__ == "__main__":
    # Test the PNR generator iterations and report collision percentage
    iterations = 500000
    test_pnr_generator(iterations)
