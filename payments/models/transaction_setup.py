import logging

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from rest_framework import serializers

from accounts.models.user_setup import MyUser
from modules.models import (
    ActiveMixin,
    DateTimeMixin,
    TransactionStatus,
    TransactionType, TicketStatus,
)
from modules.pg.paytm.wrapper.initiate_transaction_api import (
    InitiateTransaction as PaytmInitiateTransaction,
)
from modules.pg.paytm.wrapper.process_transaction_api import (
    PayTMPaymentMode,
    ProcessTransaction,
)
from modules.pg.paytm.wrapper.refund_apply_api import RefundApplyTransaction
from modules.pg.paytm.wrapper.transaction_status_api import OrderStatus, ResultCode, ResultStatus, \
    SUCCESS_CODES_LIST as PAYTM_SUCCESS_CODES_LIST, FAILED_CODES_LIST as PAYTM_FAILED_CODES_LIST, \
    PENDING_CODES_LIST as PAYTM_PENDING_CODES_LIST
from modules.utils import generate_gateway_order_id
from payments.constants import PaymentGatewayEnum, PaymentModeEnum
from payments.models.payment_gateway_setup import PaymentGatewayMode
from payments.serializers.payment_gateway_setup import (
    PaymentGatewaySerializer,
    PaymentModeSerializer,
)


class Transaction(DateTimeMixin, ActiveMixin):
    # note: INVALID_ORDER_ID is considered PENDING because sometimes paytm returns this for Pending transaction
    PAYTM_TO_INTERNAL_TRANSACTION_STATUS = {
        ResultCode.TXN_SUCCESS.value: TransactionStatus.SUCCESS,
        ResultCode.BANK_DECLINED.value: TransactionStatus.FAILED,
        ResultCode.WALLET_INSUFFICIENT.value: TransactionStatus.FAILED,
        ResultCode.INVALID_UPI_ID.value: TransactionStatus.FAILED,
        ResultCode.NO_RECORD_FOUND.value: TransactionStatus.PENDING,
        ResultCode.INVALID_ORDER_ID.value: TransactionStatus.PENDING,
        ResultCode.INVALID_MID.value: TransactionStatus.FAILED,
        ResultCode.PENDING.value: TransactionStatus.PENDING,
        ResultCode.BANK_DECLINED_REPEAT.value: TransactionStatus.FAILED,
        ResultCode.PENDING_CONFIRMATION.value: TransactionStatus.PENDING,
        ResultCode.SERVER_DOWN.value: TransactionStatus.FAILED,
        ResultCode.TXN_FAILED.value: TransactionStatus.FAILED,
        ResultCode.DECLINED_BY_REMITTER_BANK.value: TransactionStatus.FAILED,
        ResultCode.BANK_DECLINED_ACCOUNT_ISSUE.value: TransactionStatus.FAILED,
        ResultCode.MOBILE_NUMBER_CHANGED.value: TransactionStatus.FAILED,
        ResultCode.BANK_GAP_NOT_MAINTAINED.value: TransactionStatus.FAILED,
        ResultCode.INSUFFICIENT_BALANCE.value: TransactionStatus.FAILED,
    }

    # Mapping Paytm response codes to PaymentModeEnum
    PAYTM_MODE_TO_INTERNAL_MODE_MAPPING = {
        "PPI": PaymentModeEnum.WALLET,
        "UPI": PaymentModeEnum.UPI,
        "CC": PaymentModeEnum.CREDIT_CARD,
        "DC": PaymentModeEnum.DEBIT_CARD,
        "NB": PaymentModeEnum.NET_BANKING
    }

    user = models.ForeignKey(
        MyUser,
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
        blank=True,
    )
    original_transaction = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="refund_transactions",
        null=True,
        blank=True,
    )
    # this status is internal, and is not related to the payment gateway
    # if status is FAILED but gateway_transaction_status is SUCCESS,
    # then it means that we are not using this transaction for services and must be refunded
    status = models.CharField(
        max_length=1,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True,
    )
    amount = models.FloatField(validators=[MinValueValidator(0)])

    transaction_type = models.IntegerField(
        choices=TransactionType.choices, default=TransactionType.DEBIT, db_index=True
    )

    # This is the order ID generated for the payment gateway
    gateway_order_id = models.CharField(primary_key=True, max_length=30)

    # These are information from the payment gateway
    gateway_mode = models.ForeignKey(
        PaymentGatewayMode, on_delete=models.SET_NULL, null=True, blank=True
    )
    gateway_transaction_id = models.CharField(max_length=63, null=True, blank=True)
    gateway_transaction_status = models.CharField(
        max_length=1,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return self.gateway_order_id

    def is_credit(self):
        return self.transaction_type == TransactionType.CREDIT

    def is_debit(self):
        return self.transaction_type == TransactionType.DEBIT

    # function to get the transaction status
    def get_status(self):
        return self.status

    def set_status(self, status):
        if status not in TransactionStatus.values:
            raise ValueError(
                f"Invalid status: {status}. Expected one of: {TransactionStatus.values}"
            )

        if status == TransactionStatus.SUCCESS:
            self.set_status_success()
        elif status == TransactionStatus.FAILED:
            self.set_status_failed()

    # function to check transaction status is pending or not
    def is_status_pending(self):
        return self.status == TransactionStatus.PENDING

    # function to check transaction status is success or not
    def is_status_success(self):
        return self.status == TransactionStatus.SUCCESS

    def set_status_success(self):
        if not self.is_status_pending():
            return
        self.status = TransactionStatus.SUCCESS
        self.save()

    # function to check transaction status is failure or not
    def is_status_failed(self):
        return self.status == TransactionStatus.FAILED

    def set_status_failed(self):
        if not self.is_status_pending():
            return
        self.status = TransactionStatus.FAILED
        self.save()

    def set_gateway_transaction_status(self, status, gateway_transaction_id=None):
        if status not in TransactionStatus.values:
            raise ValueError(
                f"Invalid status: {status}. Expected one of: {TransactionStatus.values}"
            )
        kwargs = {
            "gateway_transaction_id": gateway_transaction_id,
        }

        if status == TransactionStatus.SUCCESS:
            self.set_gateway_transaction_status_success(**kwargs)
        elif status == TransactionStatus.FAILED:
            self.set_gateway_transaction_status_failed(**kwargs)

    # function to check transaction status is pending or not
    def is_gateway_transaction_status_pending(self):
        return self.gateway_transaction_status == TransactionStatus.PENDING

    # function to check transaction status is success or not
    def is_gateway_transaction_status_success(self):
        return self.gateway_transaction_status == TransactionStatus.SUCCESS

    def set_gateway_transaction_status_success(self, **kwargs):
        if not self.is_gateway_transaction_status_pending():
            return

        # Update transaction with additional kwargs data
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.gateway_transaction_status = TransactionStatus.SUCCESS
        self.save()

    # function to check transaction status is failure or not
    def is_gateway_transaction_status_failed(self):
        return self.gateway_transaction_status == TransactionStatus.FAILED

    def set_gateway_transaction_status_failed(self, **kwargs):
        if not self.is_gateway_transaction_status_pending():
            return

        # Update transaction with additional kwargs data
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.gateway_transaction_status = TransactionStatus.FAILED
        self.save()

    def save(self, *args, **kwargs):
        """
        status	gateway_transaction_status	meaning?
        P	P	transaction initiated but not confirmed
        P	S	status should be converted to either S
        P	F	status should be converted to F immediately
        F	P	means client is not using this transaction for services, should be refunded if it converts to S
        F	S	clients needs to be refunded
        F	F	nothing
        S	P	cannot happen
        S	S	happy case
        S	F	cannot happen
        """
        # if creating new object and object is DEBIT
        if self._state.adding:
            if self.transaction_type == TransactionType.DEBIT:
                self.gateway_order_id = generate_gateway_order_id(suffix="D")
            elif self.transaction_type == TransactionType.CREDIT:
                self.gateway_order_id = generate_gateway_order_id(suffix="C")

        # update the gateway_transaction_status post triggers
        if self.gateway_transaction_status == TransactionStatus.SUCCESS:
            if self.status == TransactionStatus.PENDING:
                self.status = TransactionStatus.SUCCESS
            elif self.status == TransactionStatus.SUCCESS:
                # self.status = TransactionStatus.REFUND
                pass

        elif self.gateway_transaction_status == TransactionStatus.FAILED:
            if self.status == TransactionStatus.PENDING:
                self.status = TransactionStatus.FAILED
            elif self.status == TransactionStatus.SUCCESS:
                # self.status = TransactionStatus.REFUND
                pass
        elif self.gateway_transaction_status == TransactionStatus.PENDING:
            if self.status == TransactionStatus.FAILED:
                # self.status = TransactionStatus.REFUND
                pass

        super().save(*args, **kwargs)

    def transaction_payload(self, callback_url=None):
        response_dict = {}
        if self.gateway_mode.gateway.name == PaymentGatewayEnum.PAYTM.value:
            if self.gateway_mode.mode.name == PaymentModeEnum.UPI.value:
                response_obj = self.paytm_upi_payload(callback_url=callback_url)
            else:
                response_obj = self.paytm_all_in_one_sdk_payload(callback_url=callback_url)

            response_dict["gateway_order_id"] = self.gateway_order_id
            response_dict["amount"] = self.amount
            response_dict["mid"] = response_obj.merchant_id
            response_dict["host"] = response_obj.base_url
            response_dict["transaction_token"] = response_obj.transaction_token
            response_dict["callback_url"] = response_obj.callback_url
            response_dict["description"] = None
            response_dict["data"] = response_obj.response["body"]

        elif self.gateway_mode.gateway.name == PaymentGatewayEnum.DEFAULT.value:
            # handle the DEFAULT gateway
            pass

        serializer = TransactionResponseSerializer(data=response_dict)
        if serializer.is_valid():
            response_dict = serializer.data
        else:
            logging.error(f"TransactionResponseSerializer error: {serializer.errors}")
        return response_dict

    def paytm_upi_payload(self, callback_url=None):
        order_id, value = self.gateway_order_id, self.amount
        paytm_obj = PaytmInitiateTransaction()
        paytm_obj.run(order_id, value, callback_url=callback_url)
        response = paytm_obj.response
        callback_url = paytm_obj.callback_url
        transaction_token = response["body"]["txnToken"]

        paytm_process_transaction_obj = ProcessTransaction()
        paytm_process_transaction_obj.run(
            order_id=order_id,
            payment_mode=PayTMPaymentMode.UPI_INTENT,
            transaction_token=transaction_token,
            callback_url=callback_url,
        )
        return paytm_process_transaction_obj

    def paytm_all_in_one_sdk_payload(self, callback_url=None):
        order_id, value = self.gateway_order_id, self.amount
        paytm_obj = PaytmInitiateTransaction()
        paytm_obj.run(order_id, value, callback_url=callback_url)
        return paytm_obj

    def paytm_order_status(self):
        order_id = self.gateway_order_id
        paytm_obj = OrderStatus()
        response = paytm_obj.run(order_id)
        gateway_transaction_id = None
        if "body" in response:
            if "txnId" in response["body"]:
                gateway_transaction_id = response["body"]["txnId"]
        response_code = response["body"]["resultInfo"]["resultCode"]

        """
            try:
        if response_code_str in PaytmTransactionStatusResponseCodesEnum.SUCCESS_CODES_LIST:
            _transaction_status_char = TransactionStatusEnum.SUCCESS_CHAR
        elif response_code_str in PaytmTransactionStatusResponseCodesEnum.FAILED_CODES_LIST:
            _transaction_status_char = TransactionStatusEnum.FAILED_CHAR
        else:
            if response_code_str in PaytmTransactionStatusResponseCodesEnum.PENDING_CODES_LIST:
                _transaction_status_char = TransactionStatusEnum.PENDING_CHAR
            else:
                _transaction_status_char = TransactionStatusEnum.FAILED_CHAR
            logger.debug("Unknown response code from PayTM: {}".format(response_code_str))
        except Exception as e:
            logger.error(e)
        """

        if response_code in PAYTM_SUCCESS_CODES_LIST:
            return TransactionStatus.SUCCESS, gateway_transaction_id
        elif response_code in PAYTM_FAILED_CODES_LIST:
            return TransactionStatus.FAILED, gateway_transaction_id
        else:
            if response_code in PAYTM_PENDING_CODES_LIST:
                return TransactionStatus.PENDING, gateway_transaction_id
            else:
                logging.error(f"paytm_order_status unknown response code: {response}")
                return TransactionStatus.FAILED, gateway_transaction_id

    def check_gateway_transaction_status(self):
        try:
            if self.gateway_mode.gateway.name == PaymentGatewayEnum.PAYTM.value:
                # return if already definite state
                if self.is_gateway_transaction_status_pending():
                    self.set_gateway_transaction_status(*self.paytm_order_status())
        except Exception as e:
            logging.error(f"check_gateway_transaction_status error: {e}")
        # add for more gateways

    def create_refund_transaction(self, amount=None):
        if not amount:
            amount = self.amount

        if self.is_credit():
            raise Exception("Cannot refund a credit transaction")

        # check if refund transaction already exists
        transaction = Transaction.objects.filter(
            transaction_type=TransactionType.CREDIT,
            original_transaction=self
        )
        if transaction.exists():
            logging.debug(f"Refund transaction already exists: {transaction}")
            raise Exception("Refund transaction already exists")

        # create the refund transaction
        refund_transaction = Transaction(
            user=self.user,
            original_transaction=self,
            status=TransactionStatus.PENDING,
            amount=-amount,
            transaction_type=TransactionType.CREDIT,
        )

        refund_transaction.save()

    def get_absolute_amount(self):
        return abs(self.amount)

    def initiate_refund_transaction(self):
        # TODO: call the gateway to create the refund transaction
        assert self.is_credit(), "Only credit transaction can be refunded"

        refund_transaction = RefundApplyTransaction()
        api_response = refund_transaction.run(
            original_order_id=self.original_transaction.gateway_order_id,
            refund_id=self.gateway_order_id,
            value=self.get_absolute_amount(),
            transaction_id=self.original_transaction.gateway_transaction_id,
        )
        logging.debug(
            f"initiate_refund_transaction for gateway_order_id: {self.original_transaction.gateway_order_id}, refund_id: {self.gateway_order_id}")
        logging.debug(f"initiate_refund_transaction response: {api_response}")

        return None

    @staticmethod
    def create_transaction(user, amount, transaction_type=TransactionType.DEBIT):
        transaction = Transaction.objects.create(
            user=user, amount=amount, transaction_type=transaction_type
        )
        transaction_payment_gateway_payload = transaction.transaction_payload()

        return transaction_payment_gateway_payload

    @staticmethod
    def get_all_gateway_transaction_status_pending_transactions(sd=None, ed=None):
        transactions = Transaction.objects.filter(
            transaction_type=TransactionType.DEBIT,
            gateway_transaction_status=TransactionStatus.PENDING
        )

        query = Q()
        if sd:
            query &= Q(created_at__gte=sd)
        if ed:
            query &= Q(created_at__lte=ed)

        transactions = transactions.filter(query)

        return transactions


class PaymentGatewayModeSerializer(serializers.ModelSerializer):
    gateway = PaymentGatewaySerializer(read_only=True)
    mode = PaymentModeSerializer()

    class Meta:
        model = PaymentGatewayMode
        fields = ("gateway", "mode")


class TransactionSerializer(serializers.ModelSerializer):
    gateway_mode = PaymentGatewayModeSerializer()

    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = (
            "active",
            "user",
            "original_transaction",
            "status",
            "amount",
            "transaction_type",
            "gateway_order_id",
            "gateway_transaction_id",
            "gateway_transaction_status",
        )


class TransactionSerializerV2(serializers.ModelSerializer):
    gateway_mode = PaymentGatewayModeSerializer()

    class Meta:
        model = Transaction
        fields = [
            "created_at",
            "original_transaction", "status", "amount",
            "transaction_type", "gateway_order_id", "gateway_mode",
            "gateway_transaction_id", "gateway_transaction_status"
        ]
        read_only_fields = (
            "created_at",
            "active",
            "user",
            "original_transaction",
            "status",
            "amount",
            "transaction_type",
            "gateway_order_id",
            "gateway_transaction_id",
            "gateway_transaction_status",
        )

    def to_representation(self, instance):
        """ Modify the representation of certain fields. """
        ret = super().to_representation(instance)
        ret['transaction_type'] = instance.get_transaction_type_display()
        ret['status'] = instance.get_status_display()
        ret['gateway_transaction_status'] = instance.get_gateway_transaction_status_display()
        return ret


class TransactionResponseSerializer(serializers.Serializer):
    # transaction = TransactionSerializer(read_only=True)
    gateway_order_id = serializers.CharField(allow_null=False, default=None)
    amount = serializers.FloatField(allow_null=False, default=None)
    mid = serializers.CharField(allow_null=True, default=None)
    host = serializers.URLField(allow_null=True, default=None)
    transaction_token = serializers.CharField(allow_null=True, default=None)
    callback_url = serializers.URLField(allow_null=True, default=None)
    description = serializers.CharField(allow_null=True, default=None)
    data = serializers.DictField(allow_null=True, default=None)

    class Meta:
        fields = "__all__"
        read_only_fields = fields
