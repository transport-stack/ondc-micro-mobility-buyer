import django

django.setup()
from modules.models import TransactionStatus
from modules.time_utils import TimePeriod

from payments.models import Transaction

# Transaction.objects.get(gateway_order_id="231013180544E5AT6VV8D").check_gateway_transaction_status()

s, e = TimePeriod.get_current_year()
for obj in Transaction.objects.filter(
        created_at__range=(s, e),
        status__in=[TransactionStatus.SUCCESS]
):
    print(obj)
    obj.check_gateway_transaction_status()
