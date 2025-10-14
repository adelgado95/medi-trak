from django.shortcuts import render
from rest_framework import serializers, viewsets
from apps.patients.models import Patient
from apps.records.models import Record
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.conf import settings

api_middleware = [import_string(mw) for mw in getattr(settings, 'REST_API_MIDDLEWARE', [])]

def apply_api_middleware(view):
    for mw_class in api_middleware:
        view = method_decorator(mw_class())(view)
    return view

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

    def validate(self, attrs):
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None)
        allow_partial = getattr(tenant, 'allow_partial_patients', False) if tenant else False
        if allow_partial:
            if not attrs.get('email'):
                raise serializers.ValidationError({'email': 'Email is required'})
        else:
            required_fields = ['first_name', 'last_name', 'ssn', 'email']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: f'Required field {field} is missing.'})
        return attrs

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

    @apply_api_middleware
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = '__all__'

class RecordViewSet(viewsets.ModelViewSet):
    queryset = Record.objects.all()
    serializer_class = RecordSerializer

    @apply_api_middleware
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

