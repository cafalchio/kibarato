import tempfile
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Promotion


def photo():
    data = BytesIO()
    Image.new('RGB', (20, 20), 'red').save(data, format='PNG')
    return SimpleUploadedFile('photo.png', data.getvalue(), content_type='image/png')


class PromotionAdminTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        settings = override_settings(MEDIA_ROOT=self.directory.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.credentials = Path(self.directory.name) / 'login.txt'
        call_command('create_promotions_user', 'promocoes', password_file=str(self.credentials), verbosity=0)
        self.user = get_user_model().objects.get(username='promocoes')
        self.client.force_login(self.user)

    def test_permissions_and_login(self):
        password = self.credentials.read_text().split('Password: ')[1].strip()
        self.assertTrue(self.client.login(username='promocoes', password=password))
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(self.credentials.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.user.get_all_permissions(), {
            f'promotions.{action}_promotion' for action in ('view', 'add', 'change', 'delete')
        })
        self.assertEqual(self.client.get(reverse('admin:index'), follow=True).status_code, 200)
        for name in ('auth_user_changelist', 'auth_user_add', 'auth_group_changelist', 'auth_group_add'):
            self.assertEqual(self.client.get(reverse('admin:' + name)).status_code, 403)

    def test_admin_upload_edit_delete_and_public_gallery(self):
        response = self.client.post(reverse('admin:promotions_promotion_add'), {
            'image': photo(), 'description': 'Almofada floral', 'price': '39.90', '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        promotion = Promotion.objects.get()
        self.assertTrue(promotion.image.storage.exists(promotion.image.name))
        response = self.client.get('/')
        self.assertContains(response, 'R$ 39,90')
        self.assertContains(response, promotion.image.url)
        self.assertContains(response, 'Almofada floral')
        self.assertEqual(self.client.post(reverse('admin:promotions_promotion_change', args=[promotion.pk]), {
            'description': 'Almofada atualizada', 'price': '49.90', '_save': 'Save',
        }).status_code, 302)
        promotion.refresh_from_db()
        self.assertEqual(promotion.price, Decimal('49.90'))
        self.assertEqual(self.client.post(reverse('admin:promotions_promotion_delete', args=[promotion.pk]), {'post': 'yes'}).status_code, 302)
        self.assertFalse(Promotion.objects.exists())
        self.assertContains(self.client.get('/'), 'Novas promoções em breve.')

    def test_invalid_upload_and_negative_price_rejected(self):
        self.client.post(reverse('admin:promotions_promotion_add'), {
            'image': SimpleUploadedFile('fake.png', b'not an image', content_type='image/png'),
            'description': 'Invalid', 'price': '10.00',
        })
        self.assertFalse(Promotion.objects.exists())
        self.client.post(reverse('admin:promotions_promotion_add'), {
            'image': photo(), 'description': 'Invalid', 'price': '-1.00',
        })
        self.assertFalse(Promotion.objects.exists())

    def test_optional_price_and_escaping(self):
        Promotion.objects.create(image=photo(), description='<script>alert(1)</script>')
        response = self.client.get('/')
        self.assertContains(response, 'Preço sob consulta')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_camera_upload_and_replacement(self):
        url = reverse('admin:promotions_promotion_add')
        self.assertContains(self.client.get(url), 'capture="environment"')
        response = self.client.post(url, {
            'image_camera': photo(), 'description': 'Foto da câmera', 'price': '20.00',
        })
        self.assertEqual(response.status_code, 302)
        promotion = Promotion.objects.get()
        previous = promotion.image.name
        response = self.client.post(reverse('admin:promotions_promotion_change', args=[promotion.pk]), {
            'image_camera': photo(), 'description': 'Nova foto', 'price': '25.00',
        })
        self.assertEqual(response.status_code, 302)
        promotion.refresh_from_db()
        self.assertNotEqual(promotion.image.name, previous)
        self.assertContains(self.client.get('/'), promotion.image.url)

    def test_camera_requires_valid_image(self):
        url = reverse('admin:promotions_promotion_add')
        for upload in ({}, {'image_camera': SimpleUploadedFile('fake.png', b'invalid')}):
            response = self.client.post(url, {'description': 'Foto', 'price': '10.00', **upload})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(Promotion.objects.exists())

    def test_visual_list_search_and_delete_confirmation(self):
        promotion = Promotion.objects.create(image=photo(), description='Tecido floral', price='29.90', unit='m')
        other = Promotion.objects.create(image=photo(), description='Almofada lisa')
        url = reverse('admin:promotions_promotion_changelist')
        response = self.client.get(url)
        self.assertContains(response, 'Promoções atuais')
        self.assertContains(response, promotion.image.url)
        self.assertContains(response, 'R$ 29,90 / m')
        self.assertContains(response, reverse('admin:promotions_promotion_change', args=[promotion.pk]))
        delete_url = reverse('admin:promotions_promotion_delete', args=[promotion.pk])
        self.assertContains(response, delete_url)
        response = self.client.get(url, {'q': 'floral'})
        self.assertContains(response, promotion.description)
        self.assertNotContains(response, other.description)
        self.assertContains(self.client.get(url, {'q': 'missing'}), 'Nenhuma promoção encontrada.')
        self.assertEqual(self.client.get(delete_url).status_code, 200)
        self.assertTrue(Promotion.objects.filter(pk=promotion.pk).exists())
        response = self.client.get(reverse('admin:promotions_promotion_change', args=[promotion.pk]))
        self.assertContains(response, 'promotion-current-photo')
        self.assertContains(response, promotion.image.url)

    def test_visual_list_empty_and_view_only_permissions(self):
        from django.contrib.auth.models import Permission
        url = reverse('admin:promotions_promotion_changelist')
        self.assertContains(self.client.get(url), 'Sua primeira promoção começa aqui.')
        promotion = Promotion.objects.create(image=photo(), description='Tecido')
        self.user.user_permissions.set(Permission.objects.filter(
            content_type__app_label='promotions', codename='view_promotion',
        ))
        response = self.client.get(url)
        self.assertContains(response, 'Ver promoção')
        self.assertNotContains(response, 'class="promotions-delete"')
        self.assertNotContains(response, 'class="promotions-edit"')
        self.assertNotContains(response, 'Adicionar promoção')
        self.assertEqual(self.client.get(reverse('admin:promotions_promotion_delete', args=[promotion.pk])).status_code, 403)

    def test_promotions_app_home_opens_all_cards(self):
        Promotion.objects.bulk_create([
            Promotion(image='promotions/example.png', description=f'Produto {index}')
            for index in range(15)
        ])
        response = self.client.get(reverse('admin:app_list', args=['promotions']), follow=True)
        self.assertRedirects(response, reverse('admin:promotions_promotion_changelist'))
        self.assertContains(response, 'class="promotions-admin-card"', count=15)
        self.assertFalse(response.context['cl'].multi_page)
        self.client.logout()
        self.assertEqual(self.client.get('/admin/promotions/').status_code, 302)

    def test_admin_home_opens_photo_dashboard(self):
        promotion = Promotion.objects.create(image=photo(), description='Tecido generico')
        response = self.client.get(reverse('admin:index'), follow=True)
        self.assertRedirects(response, reverse('admin:promotions_promotion_changelist'))
        self.assertContains(response, promotion.image.url)
        self.assertContains(response, 'class="promotions-add"')
        self.assertContains(response, '>Editar</a>')
        self.assertContains(response, '>Deletar</a>')
        self.assertNotContains(response, 'Recent actions')
        self.assertNotContains(response, 'Site administration')
        self.assertNotContains(response, 'id="nav-sidebar"')
        self.client.logout()
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response.url)

    def test_admin_price_units(self):
        for unit in ('m', 'unidade', 'kg', ''):
            with self.subTest(unit=unit):
                response = self.client.post(reverse('admin:promotions_promotion_add'), {
                    'image': photo(), 'description': 'Tecido', 'price': '1234.50', 'unit': unit,
                })
                self.assertEqual(response.status_code, 302)
                promotion = Promotion.objects.first()
                self.assertEqual(promotion.unit, unit)
                expected = 'R$ 1.234,50' + (f' / {unit}' if unit else '')
                self.assertContains(self.client.get('/'), expected)
                promotion.price = None
                self.assertEqual(promotion.display_price, 'Preço sob consulta')
        count = Promotion.objects.count()
        response = self.client.post(reverse('admin:promotions_promotion_add'), {
            'image': photo(), 'description': 'Invalid unit', 'price': '10.00', 'unit': 'invalid',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Promotion.objects.count(), count)

    def test_existing_account_is_not_changed(self):
        original = self.user.password
        with self.assertRaises(CommandError):
            call_command('create_promotions_user', 'promocoes', password_file=str(self.credentials))
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, original)

    def test_anonymous_cannot_add_promotions(self):
        self.client.logout()
        response = self.client.post(reverse('admin:promotions_promotion_add'), {
            'image': photo(), 'description': 'Unauthorized', 'price': '10.00',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Promotion.objects.exists())
