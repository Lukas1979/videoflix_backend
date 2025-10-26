from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage


ACTIVATION_EMAIL = {
    "subject": "Confirm your email",
    "template": "email/activation.html"
}
RESET_PASSWORD_EMAIL = {
    "subject": "Reset your password",
    "template": "email/password_reset.html"
}


def send_activation_email(user_email, user_name, activation_link, activation_or_reset):
    """
    After successful registration, a confirmation email will be sent to the user.
    """
    
    subject, template = _is_activation_or_reset(activation_or_reset)

    html_content = render_to_string(template, {
        "user_name": user_name, "activation_link": activation_link, "logo_cid": "logo",
    })
    msg = EmailMultiAlternatives(subject=subject, body="Please use HTML email client", from_email=None, to=[user_email])
    msg.attach_alternative(html_content, "text/html")

    _send_email(msg, user_email)


def _is_activation_or_reset(activation_or_reset):
    if activation_or_reset == "activation":
        subject = ACTIVATION_EMAIL["subject"]
        template = ACTIVATION_EMAIL["template"]
    else:
        subject = RESET_PASSWORD_EMAIL["subject"]
        template = RESET_PASSWORD_EMAIL["template"]

    return subject, template


def _send_email(msg, user_email):
    try:
        with open("static/logo_icon.png", "rb") as f:
            img = MIMEImage(f.read())
            img.add_header('Content-ID', '<logo>')
            img.add_header('Content-Disposition', 'inline', filename="logo.png")
            msg.attach(img)

        num_sent = msg.send(fail_silently=False)
        print(f"✅ Email sent to {user_email}! Quantity: {num_sent}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
