import django
django.setup()

from taskschedule.tasks import create_ticket_summary_prev_day

if __name__ == "__main__":
    create_ticket_summary_prev_day()