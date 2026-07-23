import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';

export interface DatabaseStackProps extends cdk.StackProps {
  vpc: ec2.IVpc;
}

export class DatabaseStack extends cdk.Stack {
  public readonly database: rds.DatabaseInstance;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    const dbSecurityGroup = new ec2.SecurityGroup(this, 'DatabaseSG', {
      vpc: props.vpc,
      description: 'Security Group for PostgreSQL',
      allowAllOutbound: true,
    });

    this.database = new rds.DatabaseInstance(this, 'RestaurantDatabase', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_16,
      }),

      vpc: props.vpc,

      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },

      credentials: rds.Credentials.fromGeneratedSecret('postgres'),

      databaseName: 'restaurant_rps',

      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T3,
        ec2.InstanceSize.MICRO
      ),

      allocatedStorage: 20,
      maxAllocatedStorage: 100,

      securityGroups: [dbSecurityGroup],

      publiclyAccessible: false,

      removalPolicy: cdk.RemovalPolicy.DESTROY,

      deletionProtection: false,
    });

    new cdk.CfnOutput(this, 'DatabaseEndpoint', {
      value: this.database.dbInstanceEndpointAddress,
    });
  }
}