from datetime import UTC, datetime

from models import Action, Channel, HistoryEntry, Incident

incident1 = Incident(
    id='36e3344d-aa5b-4c5a-88ef-a7eb8abe27d8',
    name='Cobro incorrecto',
    channel=Channel.WEB,
)

incident1_history = [
    HistoryEntry(
        incident_id=incident1.id,
        seq=0,
        date=datetime(2024, 10, 18, 14, 26, 22, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'He recibido mi factura de septiembre y aparece un cobro adicional por un servicio que no contraté. '
            'El servicio en cuestión se llama "Asistencia Técnica Premium", pero yo nunca solicité ni autoricé este servicio. '
            'Me di cuenta del cobro hoy, 10 de septiembre, al revisar el detalle de la factura. '
            'Solicito que se revise mi cuenta y se realice el ajuste correspondiente en el menor tiempo posible.'
        ),
    ),
    HistoryEntry(
        incident_id=incident1.id,
        seq=1,
        date=datetime(2024, 10, 18, 17, 31, 57, tzinfo=UTC),
        action=Action.CLOSED,
        description='Se hizó el ajuste en la tarjeta registrada para los pagos.',
    ),
]

incident2 = Incident(
    id='eccc588b-df31-4105-9940-86937059aff8',
    name='Internet no funciona',
    channel=Channel.MOBILE,
)

incident2_history = [
    HistoryEntry(
        incident_id=incident2.id,
        seq=0,
        date=datetime(2024, 10, 20, 14, 26, 22, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'No tengo acceso a Internet en mi hogar. El módem está encendido, pero no hay conexión. '
            'He reiniciado el equipo varias veces y verificado que el servicio esté activo en mi cuenta, '
            'pero el problema persiste. Solicito una revisión urgente del servicio.'
        ),
    ),
    HistoryEntry(
        incident_id=incident2.id,
        seq=1,
        date=datetime(2024, 10, 21, 8, 11, 41, tzinfo=UTC),
        action=Action.ESCALATED,
        description=(
            'Se ha llamado al cliente para verificar si pudo solucionar el problema con las recomendaciones '
            'planteadas por la IA, pero comenta seguir con el problema, por lo cuál se le enviará un técnico '
            'en un plazo de 2 días.'
        ),
    ),
]

incident3 = Incident(
    id='8b51a60c-07d3-4ed3-85b9-352ded0abec5',
    name='Fallo servicios',
    channel=Channel.EMAIL,
)

incident3_history = [
    HistoryEntry(
        incident_id=incident3.id,
        seq=0,
        date=datetime(2024, 10, 23, 19, 46, 40, tzinfo=UTC),
        action=Action.CREATED,
        description=(
            'Desde hace 3 días no tengo acceso a los servicios de televisión, Internet y telefonía. '
            'He revisado el estado de la conexión en el módem y en la caja de distribución, '
            'pero no he encontrado ninguna anomalía. Solicito una revisión urgente del servicio.'
        ),
    ),
]
