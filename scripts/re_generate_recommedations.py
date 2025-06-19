import django
django.setup()

from taskschedule.tasks import generate_recommendations

generate_recommendations()