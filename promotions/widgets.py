from django.contrib.admin.widgets import AdminFileWidget


class PromotionPhotoWidget(AdminFileWidget):
    template_name = "promotions/widgets/photo_input.html"

    def use_required_attribute(self, initial):
        # Either input can supply the photo; the form validates it server-side.
        return False

    def value_from_datadict(self, data, files, name):
        return files.get(f"{name}_camera") or super().value_from_datadict(data, files, name)

    def value_omitted_from_data(self, data, files, name):
        return f"{name}_camera" not in files and super().value_omitted_from_data(data, files, name)
