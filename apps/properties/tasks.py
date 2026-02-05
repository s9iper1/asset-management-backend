"""
Celery tasks for email sending.

All emails must be sent asynchronously via Celery and logged.
"""
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from apps.properties.models import EmailLog


@shared_task(bind=True, max_retries=3)
def send_email_task(self, email_log_id):
    """
    Celery task to send email asynchronously

    Args:
        email_log_id: ID of EmailLog record

    Returns:
        str: Status message
    """
    try:
        email_log = EmailLog.objects.get(id=email_log_id)

        # Send email
        email = EmailMultiAlternatives(
            subject=email_log.subject,
            body=email_log.full_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=email_log.recipients
        )
        email.send()

        # Update log
        email_log.status = 'sent'
        email_log.sent_at = timezone.now()
        email_log.save(update_fields=['status', 'sent_at'])

        return f"Email sent successfully: {email_log.subject}"

    except EmailLog.DoesNotExist:
        return f"EmailLog {email_log_id} not found"
    except Exception as exc:
        # Update log with error
        try:
            email_log = EmailLog.objects.get(id=email_log_id)
            email_log.status = 'failed'
            email_log.error_message = str(exc)[:500]
            email_log.save(update_fields=['status', 'error_message'])
        except:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
