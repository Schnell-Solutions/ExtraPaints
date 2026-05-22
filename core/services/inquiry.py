from core.services.email import InquiryEmailService


def notify_sales(
    *,
    subject: str,
    text_body: str,
    html_template: str = 'home/simple_branded_email.html',
):
    return InquiryEmailService.send(
        subject=subject,
        text_body=text_body,
        html_template=html_template,
    )


def confirm_to_customer(*, email: str, subject: str, template: str, context: dict):
    return InquiryEmailService.send_customer_confirmation(
        to_email=email,
        subject=subject,
        html_template=template,
        html_context=context,
    )
