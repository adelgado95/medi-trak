from django.shortcuts import render, get_object_or_404
from rest_framework import serializers, viewsets
from rest_framework.generics import RetrieveAPIView
from apps.patients.models import Patient
from apps.tenant.models import Tenant
from apps.records.models import Record, FlexibleRecord

from rest_framework.response import Response
from rest_framework import status

class PatientSerializer(serializers.ModelSerializer):
    ssn = serializers.CharField(required=False, allow_blank=True)
    ssn_data = serializers.JSONField(required=False)
    
    class Meta:
        model = Patient
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get("request")
        tenant = request.tenant
        hipaa_mandatory = getattr(tenant, "ssn_hippa_mandatory", False)
        rep = super().to_representation(instance)
        if hipaa_mandatory:
            rep.pop("ssn", None)
        else:
            rep.pop("ssn_data", None)
        return rep


    def __init__(self, *args, **kwargs):
        # Pop custom argument before calling super
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def validate(self, attrs):
        request = self.context.get('request')
        tenant = request.tenant
        allow_partial = tenant.allow_partial_patients
        hipaa_mandatory = tenant.ssn_hippa_mandatory

        if allow_partial:
            if not attrs.get('email'):
                raise serializers.ValidationError({'email': 'Email is required'})
        else:
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: f'Required field {field} is missing.'})
            # For HIPAA, require ssn_data; else require ssn
            if hipaa_mandatory and not attrs.get('ssn_data'):
                raise serializers.ValidationError({'ssn_data': 'Required field ssn_data is missing.'})
            if not hipaa_mandatory and not attrs.get('ssn'):
                raise serializers.ValidationError({'ssn': 'Required field ssn is missing.'})
        return attrs
    
    def validate_ssn_data(self, value):
        request = self.context.get("request")
        tenant = request.tenant
        hipaa_mandatory = tenant.ssn_hippa_mandatory
        if hipaa_mandatory:
            # Validate object structure
            if not isinstance(value, dict):
                raise serializers.ValidationError(
                    "ssn_data debe ser un objeto con number, verified y verification_date"
                )
            for field in ["number", "verified", "verification_date"]:
                if field not in value:
                    raise serializers.ValidationError(f"Campo obligatorio en ssn_data: {field}")
        else:
            # Should not be used, but allow blank
            return None
        return value


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    
    def retrieve(self, request, *args, **kwargs):
        patient = self.get_object()  # fetch patient by pk
        tenant = getattr(request, 'tenant', None)
        allowed_fields = []

        if tenant and hasattr(tenant, 'patient_visible_fields'):
            if 'all' in tenant.patient_visible_fields:
                allowed_fields = None
            else:
                allowed_fields = tenant.patient_visible_fields

        serializer = self.get_serializer(patient, fields=allowed_fields)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class RecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Record
        fields = '__all__'

class FlexibleRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlexibleRecord
        fields = '__all__'

class RecordViewSet(viewsets.ModelViewSet):
    """
    Handles patient records, using a dynamic serializer depending on tenant type.
    """

    def get_serializer_class(self):
        tenant = self.request.tenant

        if tenant.patient_records_type == Tenant.RIGID:
            return RecordSerializer
        if tenant.patient_records_type == Tenant.FLEXIBLE:
            return FlexibleRecordSerializer

    def get_queryset(self):
        tenant = self.request.tenant

        if tenant.patient_records_type == Tenant.RIGID:
            return Record.objects.filter(patient__tenant=tenant)
        if tenant.patient_records_type == Tenant.FLEXIBLE:
            return FlexibleRecord.objects.filter(patient__tenant=tenant)
        

    def perform_create(self, serializer):
        tenant = self.request.tenant
        print(self.request.data)
        patient = get_object_or_404(Patient, pk=int(self.request.data.get("patient")), tenant=tenant)
        serializer.save(patient=patient)

