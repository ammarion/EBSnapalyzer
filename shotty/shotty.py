import boto3
import botocore
import pyboto3
import click

session = boto3.Session(profile_name='sand')
ec2 = session.resource('ec2')


def filter_instances(project):
    instances = []

    if project:
        filters = [{'Name': 'tag:project', 'Values': [project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

# The main group


@click.group()
def cli():
    """Shotty Manages snapshots"""


@cli.group('snapshots')
def snapshots():
    """Commands for snapshots."""


@snapshots.command('list')
@click.option('--project', default=None,
              help="Only snapshots for this project (tag Project:<name>)")
def list_snapshots(project):
    """Commands for snapshots"""

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

    return


@cli.group('volumes')
def volumes():
    """Commands for volumes"""


@volumes.command('list')
@click.option('--project', default=None,
              help="Only Volumes for this project (tag Project:<name>)")
def list_volumes(project):
    """List EC2 Instances."""
    instances = filter_instances(project)
    for i in instances:
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
    """Commands for instances."""


@instances.command('snapshot',
                   help="Creates snapshots of all volumes")
@click.option('--project', default=None,
              help="Only Instances for this project (tag Project:<name>)")
def create_snapshots(project):
    """Create snapshots for EC2 instances."""

    instances = filter_instances(project)

    for i in instances:
        print("Stopping {0}".format(i.id))

        i.stop()
        i.wait_until_stopped()

        for v in i.volumes.all():
            print("creating snapshots of {0}".format(v.id))
            v.create_snapshot(Description="Created by Ammar's Automation")

        print("Starting {0}".format(i.id))

        i.start()
        i.wait_until_running()

    return


@instances.command('list')
@click.option('--project', default=None,
              help="Only Instances for this project (tag Project:<name>)")
def list_instances(project):
    """List EC2 Instances."""

    instances = filter_instances(project)

    for i in instances:
        tags = {t['Key']: t['Value'] for t in i.tags or []}
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('project', '<no project>')

        )))

    return


@instances.command('stop')
@click.option('--project', default=None,
              help='Only instances for project')
def stop_instances(project):
    """Stop EC2 instances"""

    instances = filter_instances(project)

    for i in instances:
        print('Stopping {0}....'.format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print(" Cloud not stop {0}. ".format(i.id) + str(e))


@instances.command('start')
@click.option('--project', default=None,
              help='Only instances for project')
def stop_instances(project):
    """Stop EC2 instances"""

    instances = filter_instances(project)
    for i in instances:
        print('Starting {0}....'.format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print(" Cloud not start {0}. ".format(i.id) + str(e))


if __name__ == '__main__':
    cli()
