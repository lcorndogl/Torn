from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.db.models.functions import TruncDate
from company.models import Employee, DailyEmployeeSnapshot


class Command(BaseCommand):
    help = "Backfill DailyEmployeeSnapshot using the last Employee record per day per employee"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-date",
            type=str,
            help="Lower bound date (YYYY-MM-DD) to include"
        )
        parser.add_argument(
            "--end-date",
            type=str,
            help="Upper bound date (YYYY-MM-DD) to include"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Chunk size for iterating aggregated rows"
        )

    def handle(self, *args, **options):
        start_date = self._parse_date(options.get("start_date"))
        end_date = self._parse_date(options.get("end_date"))
        batch_size = options.get("batch_size") or 500

        qs = Employee.objects.all()
        if start_date:
            qs = qs.filter(created_on__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_on__date__lte=end_date)

        daily_latest = (
            qs.annotate(snapshot_date=TruncDate("created_on"))
            .values("company_id", "employee_id", "snapshot_date")
            .annotate(latest_created_on=Max("created_on"))
            .order_by()
        )

        total = daily_latest.count()
        created_or_updated = 0
        self.stdout.write(f"Aggregated {total} day/employee rows to process")

        for row in daily_latest.iterator(chunk_size=batch_size):
            emp = (
                Employee.objects.filter(
                    company_id=row["company_id"],
                    employee_id=row["employee_id"],
                    created_on=row["latest_created_on"],
                )
                .order_by("-pk")
                .first()
            )
            if not emp:
                continue

            DailyEmployeeSnapshot.objects.update_or_create(
                company=emp.company,
                employee_id=emp.employee_id,
                snapshot_date=row["snapshot_date"],
                defaults={
                    "name": emp.name,
                    "position": emp.position,
                    "wage": emp.wage,
                    "manual_labour": emp.manual_labour,
                    "intelligence": emp.intelligence,
                    "endurance": emp.endurance,
                    "effectiveness_working_stats": emp.effectiveness_working_stats,
                    "effectiveness_settled_in": emp.effectiveness_settled_in,
                    "effectiveness_merits": emp.effectiveness_merits,
                    "effectiveness_director_education": emp.effectiveness_director_education,
                    "effectiveness_management": emp.effectiveness_management,
                    "effectiveness_inactivity": emp.effectiveness_inactivity,
                    "effectiveness_addiction": emp.effectiveness_addiction,
                    "effectiveness_total": emp.effectiveness_total,
                    "last_action_status": emp.last_action_status,
                    "last_action_timestamp": emp.last_action_timestamp,
                    "last_action_relative": emp.last_action_relative,
                    "status_description": emp.status_description,
                    "status_state": emp.status_state,
                    "status_until": emp.status_until,
                },
            )
            created_or_updated += 1

        self.stdout.write(self.style.SUCCESS(f"Backfill complete; snapshots written/updated: {created_or_updated}"))

    def _parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM-DD format")
