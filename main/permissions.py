from rest_framework.permissions import SAFE_METHODS
from rest_framework.permissions import BasePermission

class IsOwnerOrCreatorOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return True

        owner = getattr(obj, "user", None) or getattr(obj, "created_by", None)
        return owner == request.user
