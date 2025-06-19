from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from accounts.decorators import X_API_KEY_PARAMETERS
from coupons.models import Coupon
from coupons.serializers import CouponSerializer
from coupons.calculations import is_coupon_valid_for_user
from common.constants import NoneSerializer
from common.mixins import ViewSetPermissionByMethodMixin
from modules.views import XAPIKeyPermission, CustomJSONRenderer


@extend_schema(parameters=X_API_KEY_PARAMETERS)
class CouponViewSet(
    GenericViewSet,
    ViewSetPermissionByMethodMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    serializer_class = CouponSerializer
    queryset = Coupon.objects.filter(active=True, is_visible=True).all()
    renderer_classes = [
        CustomJSONRenderer,
    ]
    permission_classes = [IsAuthenticated, XAPIKeyPermission]
    permission_action_classes = dict(
        retrieve=(),
        list=(),
        verify=(),
    )

    @extend_schema(
        description="Check if coupon valid for user (not in use)",
        request=None,
        responses={201: NoneSerializer},
    )
    @action(detail=True, methods=["POST"])
    def verify(self, request, pk=None):
        coupon = self.get_object()
        user = request.user

        validity = is_coupon_valid_for_user(user, coupon)

        return Response(data={"data": str(validity)}, status=status.HTTP_200_OK)

    @extend_schema(tags=["Coupons"], description="Single coupon details")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Coupons"], description="List of coupons")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
