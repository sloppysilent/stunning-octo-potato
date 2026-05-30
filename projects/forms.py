from django import forms

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-textarea"}),
            "github_url": forms.URLInput(attrs={"class": "form-input"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
