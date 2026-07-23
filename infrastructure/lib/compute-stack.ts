import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface ComputeStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
}

export class ComputeStack extends cdk.Stack {
  public readonly cluster: ecs.Cluster;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    new logs.LogGroup(this, 'RestaurantLogGroup', {
      logGroupName: '/restaurant-erp/ecs',
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.cluster = new ecs.Cluster(this, 'RestaurantCluster', {
      clusterName: 'restaurant-erp-cluster',
      vpc: props.vpc,
      containerInsights: true,
    });
  }
}