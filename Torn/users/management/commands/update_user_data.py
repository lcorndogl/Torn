import requests
import environ
import time
import os
import sys
import signal
import tempfile
import platform
from collections import deque
from django.core.management.base import BaseCommand
from faction.models import Faction, FactionList
from users.models import UserList, UserRecord

# Try to import fcntl for Unix systems, handle gracefully if not available
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()

API_KEY = env('API_KEY')


class Command(BaseCommand):
    help = 'Fetch faction data from the Torn API and add a new record for each unique faction ID'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force execution even if another instance is running (bypass lock)',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock_file = None
        
        # Use platform-appropriate temp directory and file name
        if platform.system() == 'Windows':
            # On Windows, use the user's temp directory
            temp_dir = tempfile.gettempdir()
            self.pid_file_path = os.path.join(temp_dir, 'update_user_data.pid')
        else:
            # On Unix-like systems, use /tmp
            self.pid_file_path = '/tmp/update_user_data.pid'
        
        # Register signal handlers for graceful cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # SIGTERM is not available on Windows
        if platform.system() != 'Windows':
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle signals for graceful cleanup."""
        self.stdout.write(
            self.style.WARNING(
                f'Received signal {signum}. Cleaning up and exiting...'
            )
        )
        self.release_lock()
        sys.exit(0)

    def __del__(self):
        """Destructor to ensure lock is always released."""
        self.release_lock()

    def acquire_lock(self):
        """
        Acquire a file lock to prevent multiple instances from running.
        Returns True if lock is acquired, False if another instance is running.
        """
        try:
            # Check if PID file exists and if the process is still running
            if os.path.exists(self.pid_file_path):
                with open(self.pid_file_path, 'r') as f:
                    try:
                        existing_pid = int(f.read().strip())
                        # Check if process is still running
                        if self._is_process_running(existing_pid):
                            return False  # Process is still running
                        else:
                            # PID file is stale, remove it
                            os.remove(self.pid_file_path)
                    except (ValueError, OSError):
                        # Invalid PID file, remove it
                        os.remove(self.pid_file_path)
            
            # Create or open the PID file
            self.lock_file = open(self.pid_file_path, 'w')
            
            # Try to acquire an exclusive lock (only on Unix-like systems)
            if HAS_FCNTL:
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    # Lock could not be acquired
                    self.lock_file.close()
                    return False
            
            # Write the current process ID to the file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()
            
            return True
            
        except (IOError, OSError):
            # Lock could not be acquired (another instance is running)
            if self.lock_file:
                self.lock_file.close()
            return False

    def _is_process_running(self, pid):
        """Check if a process with given PID is running."""
        try:
            if platform.system() == 'Windows':
                # On Windows, use tasklist command to check if process exists
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV'],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                # On Unix-like systems, sending signal 0 checks if process exists
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.SubprocessError, ImportError):
            return False

    def release_lock(self):
        """Release the file lock and clean up."""
        if self.lock_file:
            try:
                # Try to release flock if it was used (Unix only)
                if HAS_FCNTL:
                    try:
                        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                    except (IOError, OSError):
                        pass
                self.lock_file.close()
                self.lock_file = None
                # Remove the PID file
                if os.path.exists(self.pid_file_path):
                    os.remove(self.pid_file_path)
            except (IOError, OSError):
                pass

    def handle(self, *args, **kwargs):
        # Check if --force option was provided
        force_execution = kwargs.get('force', False)
        
        # Check if another instance is already running (unless forced)
        if not force_execution and not self.acquire_lock():
            self.stdout.write(
                self.style.WARNING(
                    'Another instance of update_user_data is already running. Skipping execution.\n'
                    'Use --force to override this check.'
                )
            )
            return
        elif force_execution:
            # If forced, still try to acquire lock but don't fail if we can't
            if not self.acquire_lock():
                self.stdout.write(
                    self.style.WARNING(
                        'Force execution enabled. Running despite existing instance.'
                    )
                )

        # Log start of execution
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting update_user_data script at {time.strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )

        try:
            self._execute_main_logic()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'An error occurred during execution: {str(e)}')
            )
            raise
        finally:
            # Always release the lock when done
            self.release_lock()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Completed update_user_data script at {time.strftime("%Y-%m-%d %H:%M:%S")}'
                )
            )

    def _execute_main_logic(self):
        faction_ids = FactionList.objects.values_list(
            'faction_id', flat=True).distinct()
        call_timestamps = deque()  # Track timestamps of API calls

        factions_to_create = []
        user_records_to_create = []

        for faction_id in faction_ids:
            # Check if we need to delay to respect the rate limit
            current_time = time.time()
            while call_timestamps and current_time - call_timestamps[0] > 60:
                call_timestamps.popleft()  # Remove timestamps older than 60 seconds

            if len(call_timestamps) >= 40:
                delay = 65 - (current_time - call_timestamps[0])
                self.stdout.write(self.style.NOTICE(
                    f'Rate limit reached. Waiting for {delay:.2f} seconds...'))
                time.sleep(delay)
                call_timestamps.popleft()

            # Make the API call
            url = f'https://api.torn.com/faction/{faction_id}?selections=basic&key={API_KEY}'
            # self.stdout.write(self.style.NOTICE(f'Fetching data from {url}'))
            response = requests.get(url)
            # Record the timestamp of this call
            call_timestamps.append(time.time())

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(
                    f'Failed to fetch data for faction ID {faction_id}. Status code: {response.status_code}'))
                continue

            data = response.json()
            # self.stdout.write(self.style.NOTICE(
            #     f'Response data for faction ID {faction_id}: {data}'))

            # Check if the faction data exists
            if 'ID' in data:
                faction_data = data
                faction_list = FactionList.objects.get(
                    faction_id=faction_data['ID']
                )
                
                # Construct the rank string
                rank_data = faction_data.get('rank', {})
                rank_name = rank_data.get('name', '')
                rank_division = rank_data.get('division', 0)
                rank = rank_name + (' ' + 'I' * rank_division if rank_division > 0 else '')

                # Collect faction data for bulk creation
                factions_to_create.append(Faction(
                    faction_id=faction_list,
                    respect=faction_data['respect'],
                    rank=rank
                ))

                # Process members data
                if 'members' in faction_data:
                    for member_id, member_data in faction_data['members'].items():
                        # Use member_id as user_id if 'user_id' is missing
                        user_id = member_data.get('user_id', member_id)

                        # Ensure UserList exists
                        user_list, created = UserList.objects.get_or_create(
                            user_id=user_id,
                            defaults={'game_name': member_data['name']}
                        )

                        # Collect user record data for bulk creation
                        user_records_to_create.append(UserRecord(
                            user_id=user_list,
                            name=member_data['name'],
                            level=member_data['level'],
                            days_in_faction=member_data['days_in_faction'],
                            last_action_status=member_data['last_action']['status'],
                            last_action_timestamp=member_data['last_action']['timestamp'],
                            last_action_relative=member_data['last_action']['relative'],
                            status_description=member_data['status']['description'],
                            status_details=member_data['status'].get(
                                'details', ''),
                            status_state=member_data['status']['state'],
                            status_color=member_data['status']['color'],
                            status_until=member_data['status']['until'],
                            position=member_data['position'],
                            current_faction=faction_list
                        ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Failed to fetch faction data for faction ID {faction_id}'))

        # Bulk create factions and user records
        if factions_to_create:
            Faction.objects.bulk_create(factions_to_create)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully added {len(factions_to_create)} factions in bulk.'
            ))

        if user_records_to_create:
            UserRecord.objects.bulk_create(user_records_to_create)
            self.stdout.write(self.style.SUCCESS(
                f'Successfully added {len(user_records_to_create)} user records in bulk.'
            ))
