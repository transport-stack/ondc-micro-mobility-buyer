if __name__ == '__main__':
    import django

    django.setup()

import csv
import datetime
from django.utils.timezone import make_aware

from taskschedule.tasks import create_ticket_summary, create_ticket_summary_day_wise_aggregated, \
    create_refund_summary_day_wise_aggregated


def save_ticket_summary_to_csv(start_datetime, end_datetime):
    """
    Saves ticket summaries between start_datetime and end_datetime to a CSV file.

    Parameters:
    - start_datetime (datetime): The start datetime.
    - end_datetime (datetime): The end datetime.
    """
    # Ensure the datetime objects are timezone-aware
    start_datetime = make_aware(start_datetime)
    end_datetime = make_aware(end_datetime)

    # Call the existing function to get tickets and headers
    tickets, tickets_headers = create_ticket_summary(start_datetime, end_datetime)

    # Format datetime for the filename
    start_str = start_datetime.strftime("%Y%m%d_%H%M%S")
    end_str = end_datetime.strftime("%Y%m%d_%H%M%S")
    filename = f'ticket_{start_str}_to_{end_str}.csv'

    # Convert the data to CSV format and save it to a file
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=tickets_headers)
        writer.writeheader()
        for ticket in tickets:
            writer.writerow(ticket)


def save_ticket_summary_aggregated_to_csv(start_datetime, end_datetime):
    """
    Saves ticket summaries between start_datetime and end_datetime to a CSV file.

    Parameters:
    - start_datetime (datetime): The start datetime.
    - end_datetime (datetime): The end datetime.
    """
    # Ensure the datetime objects are timezone-aware
    start_datetime = make_aware(start_datetime)
    end_datetime = make_aware(end_datetime)

    # Call the existing function to get tickets and headers
    tickets, tickets_headers = create_ticket_summary_day_wise_aggregated(start_datetime, end_datetime)

    # Format datetime for the filename
    start_str = start_datetime.strftime("%Y%m%d_%H%M%S")
    end_str = end_datetime.strftime("%Y%m%d_%H%M%S")
    filename = f'ticket_summary_day_wise_aggregated_{start_str}_to_{end_str}.csv'

    # Convert the data to CSV format and save it to a file
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=tickets_headers)
        writer.writeheader()
        for ticket in tickets:
            writer.writerow(ticket)


def save_ticket_refund_summary_day_wise_aggregated_to_csv(start_datetime, end_datetime):
    # Ensure the datetime objects are timezone-aware
    start_datetime = make_aware(start_datetime)
    end_datetime = make_aware(end_datetime)

    # Call the functions to get aggregated data for tickets and refunds
    tickets_data, tickets_headers = create_ticket_summary_day_wise_aggregated(start_datetime, end_datetime)
    refunds_data, refunds_headers = create_refund_summary_day_wise_aggregated(start_datetime, end_datetime)

    # Prepare the refund data by renaming the columns and mapping it by date
    refunds_mapped_by_date = {
        refund['date']: {
            'refund_total_amount': refund['total_amount'],
            'refund_count': refund['refund_count']
        }
        for refund in refunds_data
    }

    # Prepare for the final headers for the CSV
    final_headers = tickets_headers + ['refund_total_amount', 'refund_count']

    # Format datetime for the filename
    start_str = start_datetime.strftime("%Y%m%d_%H%M%S")
    end_str = end_datetime.strftime("%Y%m%d_%H%M%S")
    filename = f'ticket_and_refund_summary_{start_str}_to_{end_str}.csv'

    # Merge ticket and refund data based on date
    combined_data = []
    for ticket in tickets_data:
        date = ticket['date']
        if date in refunds_mapped_by_date:
            combined_row = {**ticket, **refunds_mapped_by_date[date]}
        else:
            combined_row = {**ticket, 'refund_total_amount': 0, 'refund_count': 0}
        combined_data.append(combined_row)

    # Convert the combined data to CSV format and save it to a file
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=final_headers)
        writer.writeheader()
        for row in combined_data:
            writer.writerow(row)

    print(f"Saved combined ticket and refund summary to {filename}")


if __name__ == '__main__':
    # Example usage with specific start and end datetimes
    # start_datetime = datetime.datetime(2024, 3, 1, 0, 0, 0)
    # end_datetime = datetime.datetime(2024, 4, 1, 0, 0, 0)
    # # save_ticket_summary_to_csv(start_datetime, end_datetime)
    # save_ticket_summary_aggregated_to_csv(start_datetime, end_datetime)

    for i in range(2, 4):
        start_datetime = datetime.datetime(2024, i % 12, 1, 0, 0, 0)
        end_datetime = datetime.datetime(2024, (i + 1) % 12, 1, 0, 0, 0)
        save_ticket_refund_summary_day_wise_aggregated_to_csv(start_datetime, end_datetime)
