# snapshotalyzer-30000

Demo project to manage AWS EC2 instance snapshots

## About

This project is a demo and uses boto3 to manage
AWS EC2 instance snapshots.

## Configuring

shotty uses the configuration file created by the AWS cli. e.g.

`aws configure --profile shotty`

## Running

`pipenv run python "shotty/shotty.py <--profile=AWS_PROFILE><--region=AWS_REGION><command> <subcommand> <--project=PROJECT><--instance=InstanceID>"`

*profile* is optional, by default 'shotty' profile is used
*region* is optional, by default 'region' from connection profile is used

*command* is instances, volumes or snapshots
*subcommand* depends on command
*project* is optional
*instance* is optional for volumes list
