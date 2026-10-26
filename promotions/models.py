from decimal import Decimal
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from PIL import Image, ImageOps


def promotion_today():
    return timezone.localdate(timezone=ZoneInfo("America/Sao_Paulo"))


def image_path(instance, filename):
    return f"promotions/{uuid4().hex}{Path(filename).suffix.lower()}"


def validate_image_size(value):
    if value.size > 10 * 1024 * 1024:
        raise ValidationError("A imagem deve ter no máximo 10 MB.")


class Promotion(models.Model):
    image = models.ImageField(
        "foto", upload_to=image_path,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validate_image_size],
        help_text="JPG, PNG ou WebP. Máximo de 10 MB.",
    )
    description = models.TextField("descrição", max_length=500)
    price = models.DecimalField(
        "preço (R$)", max_digits=10, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Deixe vazio para exibir Preço sob consulta.",
    )
    unit = models.CharField(
        "unidade de venda", max_length=7, blank=True, default="",
        choices=[("", "Sem unidade"), ("m", "Metro"), ("unidade", "Unidade"), ("kg", "Quilograma (kg)")],
    )
    ends_on = models.DateField(
        "válida até", blank=True, null=True, db_index=True,
        help_text="Válida até o fim deste dia, no horário de Brasília. Depois será removida automaticamente. Deixe vazio para não expirar.",
    )

    @property
    def is_expired(self):
        return self.ends_on is not None and self.ends_on < promotion_today()

    class Meta:
        ordering = ["-pk"]
        verbose_name = "promoção"
        verbose_name_plural = "promoções"

    def __str__(self):
        return self.description[:80]

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if self.image and not self.image._committed and (update_fields is None or "image" in update_fields):
            self.image.file.seek(0)
            with Image.open(self.image.file) as source:
                image_format = source.format
                image = ImageOps.exif_transpose(source)
                image.thumbnail((480, 480), Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(output, format=image_format)
            self.image = ContentFile(output.getvalue(), name=self.image.name)
        super().save(*args, **kwargs)

    @property
    def display_price(self):
        if self.price is None:
            return "Preço sob consulta"
        amount = f"{self.price:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        suffix = f" / {self.unit}" if self.unit else ""
        return f"R$ {amount}{suffix}"
