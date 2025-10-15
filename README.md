# medi-trak
Medi-trak challenge

## Setup

Con un usuario que pertenece al grupo docker hacer
./setup_and_load.sh


## Arquitectura elegida

El sistema utiliza una arquitectura Django multi-tenant con apps separadas para pacientes, registros, usuarios y configuración de tenant. 

### Features
- **Multi-tenant arquitecture:** Cada request se asocia a un tenant usando middleware y JWT, permitiendo features dinamicas cargadas en bd y manteniendo la compatibilidad con otros clientes.
- **Serializadores dinámicos:** Los endpoints exponen y validan solo los campos configurados por el tenant, asegurando cumplimiento de reglas y privacidad.
- **Auditoría** Solo pude implementar el audit log basado en el tenant config.
- **Tests robustos:** Se usa el django suit pytest y pytest-django. 

### Trade-offs considerados
- **Flexibilidad vs. performance:** El uso de modelos flexibles (JSONField) permite adaptarse a distintos tenants, pero puede impactar la performance en consultas complejas. Se priorizó flexibilidad por los requisitos del reto. Se puede tener todo el una sola tabla con un campo extra pero tenerlo en tablas separadas es mas ordenado en mi opinion.
- **Validación dinámica:** La validación por tenant agrega complejidad al código, pero es necesaria para cumplir con el reto y podes agregar tenants solo agreando objetos a la config.
- **Implementar django-tenants y django-tenants-user**: Estos paquetes pueden cubrir hasta cierto punto la logica, pero no tengo experiencia suficiente en esos paquetes como para hacerlo en poco tiempo.
- **Usar una BD para cada cliente**: En sistemas mas grandes se pueden aislar los datos por tenant diferentes usando dn routes, pero me parecio overkill en este caso.




La arquitectura propuesta permite escalar el sistema, adaptarse a nuevos requisitos de clínicas/hospitales.
Mantener la seguridad y privacidad de los datos médicos queda pendiente de hacer
se puede hacer usando custom permission y en caso de los datos que requieren autorizacion de paciente guardar el registro de cuando un paciente da el consentimiento al tenant de ver sus datos.


Estuve off el fin de semana esto es lo que pude hacer en el tiempo.
:-)

