from rest_framework import routers

app_name = "payments"

router = routers.DefaultRouter()

# router.register(r"transaction", TransactionViewSet, "transaction")

"""
TODO:
add end point to initiate transaction
take in payload the model name and model's identification for which payment needs to initiated

eg:
"Ticket", <pnr>
"Top Up", <mobile number>
# talk to GPT about this
"""
