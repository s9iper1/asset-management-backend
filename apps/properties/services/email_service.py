"""
Email service for creating and sending emails via Celery.

All emails must be logged and sent asynchronously.
"""
from django.conf import settings
from apps.properties.models import EmailLog
from apps.properties.tasks import send_email_task


class EmailService:
    """Service for creating and sending emails"""

    @staticmethod
    def send_agency_inquiry(communication):
        """
        Create email log and send agency inquiry email via Celery

        Args:
            communication: Communication object

        Returns:
            EmailLog object
        """
        # Create email log
        email_log = EmailLog.objects.create(
            user=communication.user,
            property=communication.property,
            communication=communication,
            email_type='inquiry',
            recipients=[communication.agency.email],
            subject=communication.subject,
            body_preview=communication.initial_message[:500],
            full_body=communication.initial_message,
            status='pending'
        )

        # Queue email for sending
        task = send_email_task.delay(email_log.id)

        # Store task ID
        email_log.celery_task_id = str(task.id)
        email_log.save(update_fields=['celery_task_id'])

        return email_log

    @staticmethod
    def send_system_email(user, subject, body, email_type='system', property_obj=None):
        """
        Send system email (generic)

        Args:
            user: User object
            subject: Email subject
            body: Email body
            email_type: Type of email
            property_obj: Optional Property object

        Returns:
            EmailLog object
        """
        email_log = EmailLog.objects.create(
            user=user,
            property=property_obj,
            email_type=email_type,
            recipients=[user.email],
            subject=subject,
            body_preview=body[:500],
            full_body=body,
            status='pending'
        )

        task = send_email_task.delay(email_log.id)
        email_log.celery_task_id = str(task.id)
        email_log.save(update_fields=['celery_task_id'])

        return email_log
