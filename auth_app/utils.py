import os
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


ACTIVATION_EMAIL = {
    "subject": "Confirm your email",
    "template": "email/activation.html"
}
RESET_PASSWORD_EMAIL = {
    "subject": "Reset your password",
    "template": "email/password_reset.html"
}


def send_activation_email(user_email, user_name, activation_link, email_type):
    """
    Two types of emails can be sent: activation email or password reset email.
    """
    
    email_cfg = {"ACTIVATION_EMAIL": ACTIVATION_EMAIL, "RESET_PASSWORD_EMAIL": RESET_PASSWORD_EMAIL}.get(email_type)
    subject, template = email_cfg["subject"], email_cfg["template"]

    html_content = render_to_string(template, {
        "user_name": user_name, "activation_link": activation_link, "logo_cid": "logo",
    })
    msg = EmailMultiAlternatives(subject=subject, body="Please use HTML email client", from_email=None, to=[user_email])
    msg.attach_alternative(html_content, "text/html")

    _send_email(msg, user_email)


def _send_email(msg, user_email):
    try:
        with open(os.path.join(settings.BASE_DIR, "static", "logo_icon.png"), "rb") as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<logo>')
            img.add_header('Content-Disposition', 'inline', filename="logo.png")
            msg.attach(img)

        num_sent = msg.send(fail_silently=False)
        print(f"✅ Email sent to {user_email}! Quantity: {num_sent}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
