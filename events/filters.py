import django_filters as filters
from .models import Event


class EventFilter(filters.FilterSet):
    
    date_from = filters.IsoDateTimeFilter(field_name="date", lookup_expr="gte", help_text="Start date/time (inclusive). Format: YYYY-MM-DD (e.g. 2026-03-18)",)
    date_to = filters.IsoDateTimeFilter(field_name="date", lookup_expr="lte", help_text="End date/time (inclusive). Format: YYYY-MM-DD (e.g. 2026-03-18)",)
    
    location = filters.CharFilter(lookup_expr="icontains", help_text="Filter events by location (case-insensitive, partial match)")
    organizer = filters.NumberFilter(field_name="organizer__id",
        help_text="Filter by organizer ID (integer)",)

    class Meta:
        model = Event
        fields = ("date_from", "date_to", "location", "organizer")