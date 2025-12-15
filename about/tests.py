from django.test import TestCase
from django.urls import reverse

class AboutTests(TestCase):
    def test_about_page_access(self):
        """Тест доступности страницы "О нас" """
        url = reverse('about:about')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')