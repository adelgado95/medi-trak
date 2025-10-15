from django.shortcuts import render, get_object_or_404
from rest_framework import serializers, viewsets
from rest_framework.generics import RetrieveAPIView
from apps.patients.models import Patient
from apps.tenant.models import Tenant
from apps.records.models import Record, FlexibleRecord

from rest_framework.response import Response
from rest_framework import status

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

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

