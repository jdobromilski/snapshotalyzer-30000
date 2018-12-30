import boto3
import botocore #imported to handle aws exceptions -
                #that's where the exceptions come from
import click

session = None
ec2 = None

def filter_instances(project):
    if project:
        filters = [{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'

@click.group()
@click.option('--profile', 'profile', default='shotty',
    help="Define profile for AWS connection (Profile:<name>)")
@click.option('--region', 'region',
    help="Define AWS region (Region:<name>)")
def cli(profile,region):
    """Shotty manages snapshots"""
    global session, ec2

    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile

    if region:
        session_cfg['region_name'] = region

    session = boto3.Session(**session_cfg)
    ec2 = session.resource('ec2')


@cli.group('volumes')
def volumes():
    """Commands for volumes""" #shows up in --help for the command

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots""" #shows up in --help for the command
@snapshots.command('list')
@click.option('--project', default=None,
    help="Only instances for projects (tag Project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True, #click option,
    #a flag, False by default, sets 'list_all' to True when present.
    help="List all snapshots for each volume, not just the most recent")
def list_snapshots(project, list_all):
    "list EC2 snapshots"

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(", ".join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))

                if s.state == 'completed' and not list_all: break

    return

@volumes.command('list')
@click.option('--project', default=None,
    help="Only instances for projects (tag Project:<name>)")
def list_volumes(project):
    "list EC2 volumes"
    instances = filter_instances(project)

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or [] }
        for v in i.volumes.all():
            print(", ".join((
            v.id,
            i.id,
            v.state,
            str(v.size) + "GiB",
            v.encrypted and "Encrypted" or "Not Encrypted"
        )))

    return


@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('reboot')
@click.option('--force', 'forceflag', default=False, is_flag=True,
    help="Force EC2 instances Reboot if project not defined")
@click.option('--project', default=None,
    help="Reboot EC2 instances for projects (tag Project:<name>)")

def reboot_instances(project,forceflag):
    "Reboot EC2 instances"
    if not project and not forceflag:
        print("No project defined, breaking")
        return

    instances = filter_instances(project)

    for i in instances:
        print("Stopping {0}...".format(i.id))

        i.stop()
        i.wait_until_stopped()
        i.start()
        i.wait_until_running()

        print("Started {0}...".format(i.id))

    print("Job's done!")

    return
    ###

@instances.command('snapshot')
@click.option('--force', 'forceflag', default=False, is_flag=True,
    help="Force All EC2 instances Snapshot if project not defined")
@click.option('--project', default=None,
    help="Create snapshots of all volumes for projects (tag Project:<name>)")
def create_snapshots(project,forceflag):
    "Create snapshots for EC2 instances"
    if not project and not forceflag:
        print("No project defined, breaking")
        return

    instances = filter_instances(project)

    for i in instances:
        print("Stopping {0}...".format(i.id))

        i.stop()
        i.wait_until_stopped()

        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("   Skipping {0}, snapshot already in progress".format(v.id))
            print("   Creating snapshot of {0}".format(v.id))
            v.create_snapshot(Description="Created by SnapshotAlyzer 30000")

        print("Starting {0}...".format(i.id))

        i.start()
        i.wait_until_running()

    print("Job's done!")

    return

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances for projects (tag Project:<name>)")
def list_instances(project):
    "list EC2 instances"
    instances = filter_instances(project)

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or [] }
        print(', '.join((
        i.id,
        i.instance_type,
        i.placement['AvailabilityZone'],
        i.state['Name'],
        i.public_dns_name,
        tags.get('Project', '<no project>')
        )))

    return

@instances.command('start')
@click.option('--force', 'forceflag', default=False, is_flag=True,
    help="Force All EC2 instances Start if project not defined")
@click.option('--project', default=None,
    help='Only instances for project')
def start_instances(project,forceflag):
    "Start EC2 instances"
    if not project and not forceflag:
        print("No project defined, breaking")
        return

    instances = filter_instances(project)

    for i in instances:
        print("Starting {0}...".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print(" Could not start {0}. ".format(i.id) + str(e))
            continue

    return #send start command

@instances.command('stop')
@click.option('--force', 'forceflag', default=False, is_flag=True,
    help="Force All EC2 instances Stop if project not defined")
@click.option('--project', default=None,
    help='Only instances for project')
def stop_instances(project,forceflag):
    "Stop EC2 instances"
    if not project and not forceflag:
        print("No project defined, breaking")
        return

    instances = filter_instances(project)

    for i in instances:
        print("Stopping {0}...".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print(" Could not stop {0}. ".format(i.id) + str(e))
            continue

    return #send stop command

if __name__ == '__main__':
    cli()
