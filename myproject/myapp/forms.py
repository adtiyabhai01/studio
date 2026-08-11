from django import forms

from .models import BUDGET_CHOICES, Enquiry, Service


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ["name", "phone", "email", "service", "event_date", "city", "budget", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "field",
                    "placeholder": "Your full name",
                    "autocomplete": "name",
                    "required": True,
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "field",
                    "placeholder": "+91 98765 43210",
                    "type": "tel",
                    "autocomplete": "tel",
                    "required": True,
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "field", "placeholder": "you@example.com (optional)", "autocomplete": "email"}
            ),
            "service": forms.Select(attrs={"class": "field field-select"}),
            "event_date": forms.DateInput(
                attrs={
                    "class": "field",
                    "type": "date",
                    "placeholder": "Pick a date",
                }
            ),
            "city": forms.TextInput(
                attrs={"class": "field", "placeholder": "Your city / nearby cities"}
            ),
            "budget": forms.Select(attrs={"class": "field field-select"}),
            "message": forms.Textarea(
                attrs={
                    "class": "field field-area",
                    "rows": 4,
                    "placeholder": "Tell us about your day, the venue, and how we can help\u2026",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(is_active=True).order_by("sort_order")
        self.fields["service"].empty_label = "Select a service"
        self.fields["budget"].choices = BUDGET_CHOICES
        self.fields["phone"].help_text = ""