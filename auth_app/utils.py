import os

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage


def send_activation_email(user_email, user_name):
    """
    After successful registration, a confirmation email will be sent to the user.
    """
    
    subject = "Confirm your email"
    activation_link = os.getenv("ACTIVATE_ACCOUNT_LINK")

    html_content = render_to_string("email/activation_email.html", {
        "user_name": user_name, "activation_link": activation_link, "logo_cid": "logo",
    })
    msg = EmailMultiAlternatives(subject=subject, body="Please use HTML email client", from_email=None, to=[user_email])
    msg.attach_alternative(html_content, "text/html")

    _send_email(msg, user_email)


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
