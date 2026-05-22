from unittest.mock import patch

from django.test import TestCase

from home.models import Newsletter, NewsletterSubscriber


class NewsletterBatchTests(TestCase):
    def test_send_newsletter_batched_in_chunks(self):
        for i in range(55):
            NewsletterSubscriber.objects.create(email=f'user{i}@test.com')

        newsletter = Newsletter.objects.create(
            subject='Test',
            body='<p>Hello</p>',
        )

        with patch('core.services.newsletter.EmailMultiAlternatives') as mock_msg:
            instance = mock_msg.return_value
            instance.send.return_value = 1
            from core.services.newsletter import send_newsletter_batched

            sent, failed = send_newsletter_batched(newsletter, batch_size=50)

        self.assertEqual(sent, 55)
        self.assertEqual(failed, 0)
        self.assertEqual(mock_msg.call_count, 2)
