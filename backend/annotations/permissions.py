from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    message = "Only administrators may modify configuration."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (request.method in SAFE_METHODS or user.is_superuser)
        )


class IsManagerOrReadOnlyWorkflow(BasePermission):
    message = "Only managers may change workflow configuration."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (request.method in SAFE_METHODS or user.is_staff)
        )


class IsManagerOrAssignedAnnotator(BasePermission):
    """Managers manage jobs; annotators may work on their own assignments."""

    message = "This workflow object is not assigned to you."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if view.basename == "job" and request.method == "POST":
            return user.is_staff
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        assigned_to_id = getattr(obj, "assigned_to_id", None)
        if assigned_to_id is None and hasattr(obj, "job"):
            assigned_to_id = obj.job.assigned_to_id
        if assigned_to_id is None and hasattr(obj, "work_item"):
            assigned_to_id = obj.work_item.job.assigned_to_id
        if assigned_to_id != user.id:
            return False
        if view.basename == "job" and request.method not in SAFE_METHODS:
            return False
        return True
