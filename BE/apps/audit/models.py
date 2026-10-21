from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """One change made by an admin or staff member through the API (FEATURES 13.12).

    Only the names of the fields that were sent are kept, never their values, so passwords
    or private messages cannot end up in the log.
    """

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="audit_logs")
    actor_email = models.CharField(max_length=254, help_text="Kept even if the account is deleted")
    actor_role = models.CharField(max_length=10)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=300, db_index=True)
    resource = models.CharField(max_length=60, db_index=True, help_text="VD admin/users, topics, pois")
    object_id = models.CharField(max_length=40, blank=True)
    status_code = models.PositiveSmallIntegerField()
    fields = models.JSONField(default=list, blank=True, help_text="Tên các trường đã gửi (không lưu giá trị)")
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor_email} {self.method} {self.path} → {self.status_code}"
