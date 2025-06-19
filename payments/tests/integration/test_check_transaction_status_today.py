# import os
#
# import django
#
#
# django.setup()
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
# # from taskschedule.tasks import check_transaction_status_older
# # check_transaction_status_older()
#
# from modules.models import TransactionType
#
# from payments.models import Transaction
# from modules.time_utils import TimePeriod
#
# # Transaction.objects.get(gateway_order_id="240106212555K0W59Y4OC").initiate_refund_transaction()
#
# # s, e = TimePeriod.get_current_day()
# # for obj in Transaction.objects.filter(
# #         transaction_type=TransactionType.CREDIT
# # ):
# #     print(obj)
# #     obj.initiate_refund_transaction()
#
# # check_transaction_status_today()