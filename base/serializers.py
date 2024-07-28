from django.conf import settings
from modeltranslation.translator import translator
from rest_framework import serializers


class ModelTranslationSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        translated_fields = translator.get_options_for_model(
            self.Meta.model).fields.keys()
        for field_name in translated_fields:
            if field_name in fields:
                fields.pop(field_name)
                if self.Meta.fields != "__all__":
                    for lang in settings.MODELTRANSLATION_LANGUAGES:
                        related_field_name = f"{field_name}_{str(lang).strip()}"
                        fields[related_field_name] = serializers.CharField(
                            required=False)
        return fields


class ModelSerializerWithVerboseNames(serializers.ModelSerializer):
    def to_representation(self, instance):
        """
        Override to_representation to change field names to verbose names.
        """
        ret = super().to_representation(instance)
        new_ret = {}
        if self.Meta.fields == '__all__':
            fields = [field.name for field in self.Meta.model._meta.fields]
        else:
            fields = self.Meta.fields
        for field in fields:
            field_verbose_name = str(
                self.Meta.model._meta.get_field(field).verbose_name)
            new_ret[field_verbose_name] = ret[field]
        return new_ret


class SerializerWithVerboseNames(serializers.Serializer):
    TRANSLATED_FIELD_NAMES = {}

    def to_representation(self, instance):
        """
        Override to_representation to include translated field names in the JSON response dynamically.
        """
        ret = super().to_representation(instance)
        translated_fields = {}

        for field_name, field_value in ret.items():
            translated_name = str(
                self.TRANSLATED_FIELD_NAMES.get(field_name, field_name))
            translated_fields[translated_name] = field_value
        return translated_fields